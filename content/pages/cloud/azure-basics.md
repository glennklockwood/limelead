---
title: Azure Basics
order: 100
---

I'm still figuring out techniques and best practices for using Azure coming from
a background in HPC.  A lot of the documentation takes a
Windows/Powershell/GUI-first approach which does not compute for me, so I'm
taking notes here so I don't lose track of how to do common tasks.

So far I'm converging on using a combination of [Azure CLI][] and [Bicep][] as
the foundational tools for standing up infrastructure in Azure.  I'm not sure
this is the best way to start for people who are new to both Azure itself and
infrastructure-as-code since the declarative approach to IaC adds extra
verbosity and syntactic complexity to operations, so I think starting with the
imperative [Azure CLI][] approach is a good place to start.

[Azure CLI]: https://docs.microsoft.com/en-us/cli/azure/
[Bicep]: https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview

## Understanding authn/authz

Coming from the world of UNIX-style permissions, wrapping my head around the way
widgets in the cloud establish trust has been difficult.

In the simplest case, I wanted to understand how the access to data stored in
a storage account (like a blob container) could be granted and shared.  Before
getting there though, there's a few common concepts that have to be defined:

**Keys** are arbitrary strings of text that _authenticate_ its holder as
someone who is allowed to access something, much like the key to a door.
Also like a door key, the door doesn't care _who_ is holding the key since
the holder of a key is, by definition, allowed in the house.  And finally,
the key either opens the door or it doesn't; keys don't control what its
holder can once they're inside.

**Tokens** are collections of information that describe a set of
_authorizations_ its holder has.  It's like a driver's license; it may say
that you are allowed to drive a car only if you're wearing glasses and aren't
allowed to drive commercial vehicles.  And like a driver's license, it has
anti-counterfeiting measures (like holograms) that make it trustworthy; tokens
do this by being signed with a private key that its holder doesn't know
(like how only the DMV can make holograms).

This makes tokens self-contained; you don't need to look up someone's driver's
license in a database to see if its holder is allowed to drive a commercial
vehicle. This makes using tokens much more scalable. It also means if a token
is stolen, there's no way to invalidate it since there's no central database
that stores it. For this reason, tokens are usually encoded with expiration
dates in their payload and are meant to live only for short periods of time.

Understanding keys and tokens means we can now understand the three ways that
access to a storage account can be granted: shared keys, SAS tokens, and OAuth
tokens.

### Shared keys

_Shared keys_, _storage account keys_, or just _account keys_ allow its holder
(regardless of who they are) to access everything in a storage account.  Shared
keys are like a skeleton key that give limitless access, so you really don't
want to use these since if they are ever leaked or stolen.  Storage account keys
also don't have an expiration date, so if one gets stolen it must be "rotated,"
the process where an old key is invalidated and replaced by a new shared key.

To authorize using a shared key in Azure Storage, you have to stick it in the
`Authorization` part of a REST request header.

### SAS tokens

_Shared access signatures (SAS)_ are tokens that have expiration dates,
restrictions on what they allow the holder to do, and limitations on what
contents the holder may access.  Unlike shared keys, SAS tokens are embedded in
the URI itself rather than a REST request header.  Strange distinction, but it
makes it easier to pass a single string that includes the resource location
(`https://whatever.blob.core.windows.net/`) and the authentication and
authorization (embedded in the SAS token at the end of the URI, like
`?sig=Rmj0%2B4AN...`) to someone so they can download, say, a file out of
OneDrive.

SAS tokens are self-contained, so you can create as many SAS tokens with
different restrictions as you want; all you have to do is roll up a set of
permissions into a special payload string (creatively called the
"string-to-sign") and then _sign_ it using a secret that only you and the
storage account know.  This combination of permissions string and signature
_is_ the SAS token.  So if Jane Doe shows up with a SAS token, Azure verifies
that it is legitimate by following the exact same process used to create the SAS
token using the permissions string provided by Jane and the same secret.  If
the signature that pops out when Azure does this doesn't match the signature
provided by Jane, that means Jane's SAS token was signed using the wrong
secret and she's not authorized.

What exactly is that secret that's used to sign SAS tokens?  There are actually
three types of secrets that can be used, and that results in three flavors of
SAS tokens.

**Account SAS** tokens are signed using the storage account key.  Because you
cannot generate an account SAS without having the storage account key, this
type of SAS token is able to authorize a wide range of actions such as changing
the properties of the different storage account services (blob, file, etc) and
can carry the authority to do a lot of damage. Relying on account SAS also
relies on having storage account keys accessible wherever account SAS gets
generated which is risky, so using account SAS is not super safe.

**Service SAS** tokens are also signed using the storage account key, but they
can only be used to access a single storage service (blob, file, etc). Unlike
account SAS, service SAS can also have a server-side database that connects SAS
keys to specific permissions (called [storage access policies][]) that
supersedes whatever authorizations are embedded in the SAS token. This means
that a service SAS key can be completely deactivated by revoking its
authorizations in the storage access policy. If Jane Doe shows up with a signed
service SAS with wide-ranging permissions but its associated storage access
policy says it has no permissions, that SAS key won't allow Jane to do anything.

**User delegation SAS** is signed using a _user delegation key_ instead of a
storage account key. User delegation keys are issued by the storage account's
management API upon request, but only authorized AAD users with the correct role
are allowed to have the storage account generate them.  When a user delegation
key is issued, it also includes a pair of unique identifiers
(`signedObjectId`/`skoid` and `signedTenantId`/`sktid`) that get embedded in
the SAS token to indicate the AAD user whose user delegation key was used to
sign the SAS token.  This way, any time Jane Doe shows up with a user
delegation SAS, Azure can verify authorization by

1. looking up the AAD user whose user delegation key was allegedly used to sign
   the token,
2. looking up the role-based access controls (RBAC) associated with that user
3. verifying that the SAS token does not include permissions that exceed what
   AAD says that user's RBAC permissions should be
4. verifying that the user delegation key associated with that AAD user is still
   valid and reproduces the signature provided by Jane

Because the server side (the storage account) retains a mapping of user
delegation keys to users, and users can be mapped to specific RBAC
authorizations via AAD, the limitations of a user delegation SAS can be changed
after its creation just like with account SAS tokens with storage access
policies. And like with account SAS + storage access policies, stolen user
delegation SAS tokens can be invalidated by revoking the user delegation keys
used to generate them.

[stored access policies]: https://docs.microsoft.com/en-us/rest/api/storageservices/define-stored-access-policy

### OAuth Tokens

You can also use bearer tokens issued by AAD to authenticate and authorize
access to storage accounts very simply.  The flow is

1. You authenticate with AAD and get a bearer token from AAD
2. Pass this bearer token in the `Authorization` part of a REST request header
3. Profit

This is pretty powerful since an AAD identity (or _principal_) can be assigned
to not just you (a person), but an app or a VM itself.  In the case of VMs, you
can further use _managed identities_ that are automatically created and
destroyed along with VMs to automatically manage the permissions of VMs to
access data in storage accounts.

See [Authorize access to blobs using Azure Active Directory][] for a more
detailed explanation of how this works.

[Authorize access to blobs using Azure Active Directory]: https://learn.microsoft.com/en-us/azure/storage/blobs/authorize-access-azure-active-directory

## Managed Identities

If your VM has an assigned managed identity, you can get it (and a bearer token)
using

```
curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true -s
```

Of note, `169.254.169.254` is a magical REST endpoint in Azure that stores
instance metadata called the [Azure Instance Metadata Service (IMDS)][imds].
Poking this endpoint from inside a VM is how you inspect metadata about
yourself.

More information on how to use IMDS to give your VM access to other resources
on [How to use managed identities for Azure resources on an Azure VM][].

[How to use managed identities for Azure resources on an Azure VM]: https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/how-to-use-vm-token
[imds]: https://learn.microsoft.com/en-us/azure/virtual-machines/linux/instance-metadata-service

## Working in a big subscription

Most online documentation assume you have your own developer subscription to
play around in.  In reality, most people thrown head-first into Azure have one
or more existing subscriptions that are subject to complex regional restrictions
and quotas, so here's some of the problems I encountered while playing around.

### VM SKU / hypervisor conflicts

I tried this:

```
$ az deployment group create --resource-group glock-rg \
                             --template-file template.bicep \
                             --parameters @parameters.json

The selected VM size 'Standard_A1_v2' cannot boot Hypervisor Generation '2'. If
this was a Create operation please check that the Hypervisor Generation of the
Image matches the Hypervisor Generation of the selected VM Size. If this was
an Update operation please select a Hypervisor Generation '2' VM Size.
```

It turns out this is because my `properties.storageProfile.imageReference.sku`
was `18_04-lts-gen2` - the `gen2` was the incompatible part.  To find all the
compatible VMs:

```
$ az vm image list-skus --location westcentralus --publisher Canonical --offer UbuntuServer --output table
Location       Name
-------------  --------------------
westcentralus  12.04.5-LTS
westcentralus  14.04.0-LTS
westcentralus  14.04.1-LTS
westcentralus  14.04.2-LTS
...
```

See [this page](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/cli-ps-findimage) for the full documentation.
>>>>>>> reorder a bunch of pages based on popularity/relevance
