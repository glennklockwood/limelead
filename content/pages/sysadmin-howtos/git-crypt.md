---
title: Using git-crypt
---

## Set up GPG

You need to use `--full-gen-key` or else you get something that doesn't seem to
work right with git crypt:

    glock@laptop1$ gpg --full-gen-key

Then export the public key:

    glock@laptop1$ gpg --list-secret-keys --keyid-format=long

    glock@laptop1$ gpg --armor --export B401B9A0A9E1B1A4

Assuming your GPG key id is `B401B9A0A9E1B1A4`.  You need to use
`--keyid-format=long` or else git-crypt will not be able to find it.

## Set up a git repo

Go into a git repo.  Then

    glock@laptop1$ git crypt init

    glock@laptop1$ git crypt add-gpg-user B5CC247C50CB63A3

This will silently commit some new stuff to the repository.  Then tell git-crypt
that a file is to be encrypted by creating or editing `.gitattributes`:
    
    glock@laptop1$ cat .gitattributes
    settings.sh filter=git-crypt diff=git-crypt

Then commit _just_ this `.gitattributes` file.  Leave the actual file you want
to encrypt alone for now.

    glock@laptop1$ git add .gitattributes
    glock@laptop1$ git commit -m "add gitattributes"

Then add the file:

    glock@laptop1$ git add settings.sh
    glock@laptop1$ git commit -m "add file to be encrypted"

The file will be unencrypted at rest, but if you `git push` it will be encrypted
before being uploaded.

## Add other users to git-crypt

In order to let other users decrypt files, someone who already can decrypt files
must add their publickey.

Let's say a second person's (`mary`'s) laptop is called `laptop2` and the person
who initialized the above (`glock`) is using `laptop1`.  The new person should
create their GPG key as above:

```
laptop2$ gpg --full-gen-key

laptop2$ gpg --list-secret-keys --keyid-format=long
/Users/me/.gnupg/pubring.kbx
-------------------------------
sec   ed25519/B5CC247C50CB63A3 2022-03-14 [SC] [expires: 2024-03-13]
      2307BF889A46DDE3B4B5C766B5CC247C50CB63A3
uid                 [ultimate] Mary Berry <mary@berry.com>
ssb   cv25519/64776E3CDA70A0A6 2022-03-14 [E] [expires: 2024-03-13]
```

Then export the public key:

```
laptop2$ gpg --armor --export B5CC247C50CB63A3
-----BEGIN PGP PUBLIC KEY BLOCK-----

mDMEYi+PwRYJKwYBBAHaRw8BAQdApHnj8xmTdg+Mh3GE72N5JLXGZvcQ/BGz2WUJ
iXk70OK0LEdsZW5uIEsuIExvY2t3b29kIDxnbGVubmtsb2Nrd29vZEBnbWFpbC5j
b20+iJoEExYKAEIWIQQjB7+Imkbd47S1x2a1zCR8UMtjowUCYi+PwQIbAwUJA8Jn
AAULCQgHAgMiAgEGFQoJCAsCBBYCAwECHgcCF4AACgkQtcwkfFDLY6Pl9wD/UDjV
Ay5EC5uS9SJ2XVOJOt8L4BoUy3rV6FdO7iaASmMA/2t01Vev+l3UnecVvnrA8EjM
iZnV35tnxwMTGgEqBT8JuDgEYi+PwRIKKwYBBAGXVQEFAQEHQKz2qNEB4fOsOoYC
V+Wfw9S0FNbFcbwWmcbWbhGKBwtPAwEIB4h+BBgWCgAmFiEEIwe/iJpG3eO0tcdm
tcwkfFDLY6MFAmIvj8ECGwwFCQPCZwAACgkQtcwkfFDLY6MdpQD+P9kxiGS4rG75
ef6gU1B/JIWuc8mWfatBikO395BPrBYBANfX03lOe/eANRYOEUzqlHq17H8b8O/r
Sld+MjNxYzII
=WipN
-----END PGP PUBLIC KEY BLOCK-----
```

Mary should then send this public key to glock.  Then glock has to first import
that public key (e.g., using copy paste):

```
glock@laptop1$ gpg --import -
<paste the public key here, then ctrl+d>

gpg: key B5CC247C50CB63A3: public key "Mary Berry <mary@berry.com>" imported
gpg: Total number processed: 1
gpg:               imported: 1
```

Then this public key can be added to our git repo:

```
glock@laptop1$ git crypt add-gpg-user --trusted B5CC247C50CB63A3
```

Note that you have to use `--trusted` because we didn't `gpg --edit-key` and
issue the `trust` command.  You can trust the key after importing if you want.

glock then pushes all of this up, and mary can pull it down:

```
mary@laptop2$ git clone git@github.com:glennklockwood/secret.git
```

Our encrypted file is still encrypted at this point, but mary can unlock the
repository now that it's cloned:

```
mary@laptop2$ git crypt unlock
```

This will prompt for a password, but once it's unlocked, it's unlocked for good.

## Pitfalls

If mary were to run `git crypt add-gpg-user` herself instead of having glock do
it, the repository would throw errors like this:

```
mary@laptop2$ git crypt unlock
git-crypt: error: encrypted file has been tampered with!
error: external filter '"/usr/local/bin/git-crypt" smudge' failed 1
error: external filter '"/usr/local/bin/git-crypt" smudge' failed
fatal: settings.sh: smudge filter git-crypt failed
Error: 'git checkout' failed
```

This is because mary can't add her own key to a repository she just cloned; that
would allow anyone to just add themself to a repo to decrypt everything in it!
See below for how this works.

## How it works

When you `git crypt init`, a symmetric key is generated used to encrypt files in
the repository.  You then use your GPG key to asymmetrically encrypt that key,
and your asymmetrically encrypted version of that symmetric key gets stored in

```
.git-crypt/keys/default/0/2307BF889A46DDE3B4B5C766B5CC247C50CB63A3.gpg
```

As you add more users using `git crypt add-gpg-user`, you are using the supplied
public key to create a new asymmetrically encrypted version of the symmetric key
which also gets stored in the above directory.
