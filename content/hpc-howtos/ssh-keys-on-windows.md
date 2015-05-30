---
title: Configuring SSH Keys on Windows
shortTitle: SSH Keys on Windows
date: 2013-09-17T00:00:00-07:00
template: page.jade
parentDirs: [ hpc-howtos ]
---

## Introduction

At SDSC, we allow key-based authentication to access our supercomputers in
addition to the usual password-based and <a href="http://www.globus.org/toolkit/security/index.html">Globus-based</a> 
authentication mechanisms.  Setting up ssh keys on Linux and Mac desktops is
quite simple, but the process is a lot more involved on Windows.  Because the
steps required to use key-based authentication to log into Gordon and Trestles
is a common request from our Windows users, below is an illustrated guide on 
exactly how to do this.

Before you begin, you will need to download two pieces of software:

1. PuTTY, my preferred SSH client for Windows (you may already have this)
2. <code>puttygen.exe</code>, part of the PuTTY suite, which can generate SSH keys

Both can be downloaded from [the PuTTY website][putty website] as standalone
executables that don't need to be "installed", so it's convenient to download
both <code>.exe</code> files on to your desktop and just run them from there.

## Generating an SSH Key

As its name suggests, <code>puttygen.exe</code> is the program you'll have to
launch to generate an SSH key for you to use to log into a remote system using
key-based authentication.  Start it up, and you should see a screen similar to
the one below:

{{<figure src="puttygen1.png" link="puttygen1.png" alt="puttygen main screen">}}

The first thing you need to do is change the "<samp>Number of bits in a 
generated key</samp>" to at least <code>2048</code> (<span style="color:red">red arrow</span>).
**The default value of 1024 bits is no longer considered secure**, so please
don't forget to do this step!</p>

Then press the <code>Generate</code> button (<span style="color:green">green
arrow</span>) and you will see this:


{{<figure src="puttygen2.png" link="puttygen2.png" alt="puttygen key generation screen">}}

You will need to wiggle your mouse over the blank area below the progress
bar to feed <code>puttygen</code> enough randomness to generate an unpredictable
ssh key for you.  Once the progress bar is full, you will be presented with
your ssh key, which takes the form of a bunch of letters and numbers.

First, copy the public key that <code>puttygen</code> created into your
clipboard:

{{<figure src="puttygen3.png" link="puttygen3.png" alt="puttygen copy publickey to clipboard">}}

Then you will need to paste this into your account on Gordon or Trestles.
SSH to one of those machines (logging in with your password, since we haven't
set up key-based authentication yet) and edit <code>.ssh/authorized_keys</code>:

<pre>
$ <kbd>nano -w .ssh/authorized_keys</kbd>
</pre>

Note the <kbd>nano -w</kbd>; if you forget to specify <kbd>-w</kbd>, word
wrap will be enabled and bungle up the format of your <code>authorized_keys</code>
file!  You don't want this, because each line of <code>authorized_keys</code>
must be an entire ssh publickey.  You should already have one publickey in
there that was set up the very first time you logged into your account:

<pre style="background:black;color:#CCC"><span style="color:black;background:#CCC">  GNU nano 1.3.12             File: g09job.qsub                                 </span>

ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5RnzGKXvfcIcJOnyo3gz22qz763WP7jgnD9pndZyaT4$





<span style="color:black;background:#CCC">^G</span> Get Help  <span style="color:black;background:#CCC">^O</span> WriteOut  <span style="color:black;background:#CCC">^R</span> Read File <span style="color:black;background:#CCC">^Y</span> Prev Page <span style="color:black;background:#CCC">^K</span> Cut Text  <span style="color:black;background:#CCC">^C</span> Cur Pos
<span style="color:black;background:#CCC">^X</span> Exit      <span style="color:black;background:#CCC">^J</span> Justify   <span style="color:black;background:#CCC">^W</span> Where Is  <span style="color:black;background:#CCC">^V</span> Next Page <span style="color:black;background:#CCC">^U</span> UnCut Text<span style="color:black;background:#CCC">^T</span> To Spell</pre>

So move the cursor down to an empty line (or create a new line by pressing
return), then paste in the line that you copied from <code>puttygen</code>:

<pre style="background:black;color:#CCC"><span style="color:black;background:#CCC">  GNU nano 1.3.12             File: g09job.qsub                                 </span>

ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5RnzGKXvfcIcJOnyo3gz22qz763WP7jgnD9pndZyaT4$
$Zk9qyY7Wnylxy3q5Py8fTggmtKQ+3YinbnGr




<span style="color:black;background:#CCC">^G</span> Get Help  <span style="color:black;background:#CCC">^O</span> WriteOut  <span style="color:black;background:#CCC">^R</span> Read File <span style="color:black;background:#CCC">^Y</span> Prev Page <span style="color:black;background:#CCC">^K</span> Cut Text  <span style="color:black;background:#CCC">^C</span> Cur Pos
<span style="color:black;background:#CCC">^X</span> Exit      <span style="color:black;background:#CCC">^J</span> Justify   <span style="color:black;background:#CCC">^W</span> Where Is  <span style="color:black;background:#CCC">^V</span> Next Page <span style="color:black;background:#CCC">^U</span> UnCut Text<span style="color:black;background:#CCC">^T</span> To Spell</pre>

Again, **be sure that word wrap didn't break the line you pasted from 
<code>puttygen</code> into multiple lines**.  Once you've done this, 
<kbd>ctrl+x</kbd> to exit, and be sure to save your changes.

Once you've pasted your publickey from <code>puttygen</code> into your remote
account's <code>authorized_keys</code> file on Gordon/Trestles, go back to your
<code>puttygen</code> window.  We still have to save the privatekey 
corresponding to the publickey you just pasted.

Before saving your private key though, note that you can add a <samp>Key 
passphrase</samp> (<span style="color:red">red arrow</span> below) to your ssh 
key to encrypt it.  This is essentially password-protecting your password and 
I _strongly_ recommend doing this even though it's optional--without 
encrypting your ssh key with a passphrase, anyone who can access your ssh key 
file will be able to log into your Gordon/Trestles account without needing to 
know your login password.  On Windows, this is a very real hazard.

{{<figure src="puttygen4.png" link="puttygen4.png" alt="puttygen adding encryption to key">}}

Now you have to save the private part of your ssh key by clicking the
<samp>Save private key</samp> button (<span style="color:red">red arrow</span> 
below):

{{<figure src="puttygen5.png" link="puttygen5.png" alt="puttygen save private key">}}

If you disregarded my advice and are leaving your privatekey unencrypted,
you will get a warning.  Again, _don't leave your ssh key unencrypted_
on Windows unless you are sure you know what you are doing--this typically means
editing the file access permissions for the keyfile you will be generating to
make sure nobody on your network can access this file and use it to break into
your account on Gordon/Trestles.

{{<figure src="puttygen6.png" link="puttygen6.png" alt="puttygen unencrypted key warning">}}

Save your private key somewhere safe--definitely don't put it in a shared
folder or anywhere someone can easily steal it from you.  This key file is all
you (or whoever else gets ahold of it) needs to get into your account if you
did not encrypt it with a passphrase.

{{<figure src="puttygen7.png" link="puttygen7.png" alt="puttygen saving encrypted private key">}}

## Using the Key with PuTTY

Now that you've generated your <code>.ppk</code> private key file, you can
configure PuTTY to use that key before presenting you with a password prompt
whenever you try to log in.  If you don't have a profile already created for
Gordon or Trestles in PuTTY, you can make one by doing something like

1. Enter <kbd>gordon.sdsc.edu</kbd> under <samp>Host Name (or IP address)</samp>
2. Enter <kbd>Gordon</kbd> under <samp>Saved Sessions</samp>
3. Pressing the <samp>Save</samp> button

If you already have a saved profile, be sure to <samp>Load</samp> it <span
style="color:red">red arrow</span> below) before proceeding--this will allow 
us to modify it instead of having to create a new profile for the ssh key we 
just generated.

{{<figure src="putty1.png" link="putty1.png" alt="putty load existing profile">}}

On the list of options on the left side of the PuTTY window, scroll down to
<samp>Connection</samp>, then expand it, expand the <samp>SSH</samp> tree, then
click the <samp>Auth</samp> category.  You will be presented with something like
this:

{{<figure src="putty2.png" link="putty2.png" alt="putty load private key ppk">}}

Click the <samp>Browse</samp> button under the <samp>Private key for 
authentication</samp> input box, then find the <code>PPK</code> file we just
saved in <code>puttygen</code> and load it:

{{<figure src="putty3.png" link="putty3.png" alt="putty find ppk file">}}

Navigate back to the <samp>Session</samp> option on the left side of the
PuTTY window and click <samp>Save</samp> to save the location of your 
<code>PPK</code> file with your profile for Gordon (or Trestles):

{{<figure src="putty4.png" link="putty4.png" alt="putty save updated profile with ppk">}}

Following this, you should be able to now <samp>Open</samp> the profile and
have your private key used whenever you try to connect.  As a bonus, this
<code>PPK</code> file can be used with programs like [WinSCP][winscp website]
in much the same way.  Using key-based authentication is arguably better than
simply saving your login password in WinSCP, and if your key is ever stolen,
you can de-activate it by removing it from the <code>authorized_keys</code>
file in your account on Gordon or Trestles and repeat this process to generate
a new key.

<!-- References -->
[putty website]: http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html
[winscp website]: http://winscp.net/eng/index.php
