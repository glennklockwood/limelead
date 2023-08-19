---
title: Understanding Authentication and Authorization
shortTitle: authn and authz
order: 120
---

Coming from the world of UNIX-style permissions, wrapping my head around the way
cloud services establish trust and permissions has been difficult.  Here are my
notes based on my learnings.

## Azure Active Directory

Azure Active Directory (AAD) is the identity and access management system for
Azure and is the source of truth for who is who and what they are allowed to do.
Despite its name, AAD is not really related to regular Active Directory.

A person is represented within AAD as a _principal_ and is kind of like a user
account in a Linux system.  And like a Linux user, a principal doesn't have to
map to map only to a person; it can also represent an application (in which case
it would be called a _service principal_).  A group is also a type of principal.
Resources you provision in Azure (VMs, Kubernetes clusters, serverless
functions) can also be principals.

### Associating principals with permissions

The mapping between a principal and what that principal is allowed to access is
also stored in AAD in the form of _roles_ and _scopes_.  To create such a _role
assignment_, you'd do something like

    az role assignment create \
        --role "Storage Blob Data Contributor" \
        --assignee 3a1e482e-aa02-7fbb-87d3-920af417280c \
        --scope /subscriptions/d45c562f-6dcd-02fa-8030-168d77b665be/resourceGroups/myResourceGroup/providers/Microsoft.Storage/storageAccounts/myStorageAccount

This creates a mapping between the principal
`3a1e482e-aa02-7fbb-87d3-920af417280c` (which could be a user principal, service
principal, etc.) and the predefined role of `Storage Blob Data Contributor`.
The scope shown indicates that this assignment and role only applies to requests
that target the resource `/subscriptions/d45...`.  That scope maps to a specific
storage account  (`myStorageAccount`) in a specific resource group
(`myResourceGroup`) in a specific subscription (`d45c562f...`) in this example,
but you can widen the scope by chopping off  the specific storage account name
or the specific resource group.

### Authenticating principals

In standard Linux permissions, authentication is easy; if you are logged in as
a user, you can do everything that user can do until you log out.  The Linux
kernel is what enforces those permissions and checks to make sure that you
are allowed to, say, open a file or run an application.

In Azure though, there is no notion of being logged in to AAD.  Every
request you make of a service has to be authenticated and authorized since
requests can come from anywhere in the world, not just anyone logged in to
a machine. The standard way this authentication is done is by embedding
_bearer tokens_ in the http headers of the REST requests that are used to
interact with different services.

{% call alert(type="info") %}
Sometimes it may seem like you're "logged in" to Azure (for example, you don't
have to authenticate every time you use the Azure CLI), but that "logged in"
experience is actually achieved using bearer tokens and [refresh tokens][].

[refresh tokens]: https://learn.microsoft.com/en-us/azure/active-directory/develop/refresh-tokens
{% endcall %}


Only certain AAD principals (service principals and managed identities) can
request a bearer token, and anyone who has (or "bears") a valid bearer token is
authenticated as that principal.  User principals, group principals, and other
principals _cannot_ request bearer tokens though, since users are meant to access
services through client applications, and the client applications are what would
use bearer tokens.  Instead, users authenticate to apps using one of several
supported [token grant flows][], and then that app (which has a service principal)
can request bearer tokens on behalf of the user.

[token grant flows]: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-device-code

There's a lot more detail bured in the AAD docs for those interested.  For example, you can inspect the schemata of different AAD principals by reviewing [this page](https://learn.microsoft.com/en-us/azure/active-directory/hybrid/cloud-sync/concept-attributes) or playing with the [MS Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer).

## Azure Storage

Let's walk through how this applies to accessing a blob storage account.

### OAuth and Managed Identities

You can use OAuth bearer tokens issued by AAD to authenticate and authorize
access to storage accounts very simply.  The flow is

1. You authenticate with AAD as a service principal or managed identity
2. You request a bearer token from AAD
2. Pass this bearer token in the `Authorization` part of a REST request header
3. The server decodes the bearer token, confirms the signature, and authorizes the request

_Managed identities_ are AAD principals that are automatically created and
destroyed when some other resource is created and destroyed.  For example, you
can provision a VM with a managed identity and then authorize that VM
(specifically its managed identity) to access a storage account without having
to pass any secrets (keys or signed tokens) into the VM first.

This works because every VM can access the [Azure Instance Metadata Service
(IMDS)][imds] which is a magic REST endpoint that allows you to inspect
properties of a VM from inside that VM.  If a VM has a managed identity, you
can retrieve a bearer token that reflects that identity with a simple REST
request:

    curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fmanagement.azure.com%2F' -H Metadata:true -s

where `169.254.169.254` is the magical REST endpoint for the [IMDS][imds].  The bearer token you get back will be a giant string that starts with something like `eyJ0eXa...`.

You can then pass this bearer token along with a request to the storage account using curl:

    curl -s -H 'x-ms-version: 2019-02-02' \
            -H 'Authorization: Bearer eyJ0eXA...' \
            'https://mystorageaccount.blob.core.windows.net/mycontainer?restype=container&comp=list'

If you are using something nicer than curl to access a storage account from inside a VM though, odds are that it is smart enough to retrieve a bearer token for you.  Tools like blobfuse and azcopy just need to be told that you wish to authenticate via managed identities (also known as "MSI" - Managed Service Identity) and they will handle talking to IMDS on your behalf.  So you never have to deal with keys or signed tokens yourself--it's all taken care of as long as your VM has a managed identity that is authorized to access your storage account.

More information on how to use IMDS to give your VM access to other resources
on [How to use managed identities for Azure resources on an Azure VM][].

[How to use managed identities for Azure resources on an Azure VM]: https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/how-to-use-vm-token
[imds]: https://learn.microsoft.com/en-us/azure/virtual-machines/linux/instance-metadata-service
[Authorize access to blobs using Azure Active Directory]: https://learn.microsoft.com/en-us/azure/storage/blobs/authorize-access-azure-active-directory

If you authorize a service principal to access your storage account, the process
is very similar.  Instead of hitting the IMDS endpoint though, you have to use the Microsoft Auth Application like this:

    curl -s -X POST \
        -d 'grant_type=client_credentials' \
        -d 'client_id=fadd0a22-eb9d-c0d8-30ef-c841a67c9d28' \
        -d 'client_secret=SECRET' \
        -d 'scope=https://mystorageaccount.blob.core.windows.net/.default' \
        https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token

This requires a little more setup since you have to have generated a client
secret for your service principal (`fadd0a22...` in the above example).  You
can find out more about how this works in the [client credentials auth flow][]
documentation.

[client credentials auth flow]: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow

In addition to using OAuth to authenticate storage account access, storage
accounts support several other auth modes though.  Let's talk about those next.

### Shared keys

_Shared keys_, _storage account keys_, or just _account keys_ allow their holder
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

**Account SAS** tokens are signed using the storage account key discussed in
the previous section.  Because you cannot generate an account SAS without having
the storage account key, this type of SAS token is able to authorize a wide
range of actions such as changing the properties of the different storage
account services (blob, file, etc) and can carry the authority to do a lot of
damage. Relying on account SAS also relies on having storage account keys
accessible wherever account SAS gets generated which is risky, so using
account SAS is not super safe.

**Service SAS** tokens are also signed using the storage account key, but they
can only be used to access a single storage service (blob, file, etc). Unlike
account SAS, service SAS can also have a server-side database that connects SAS
keys to specific permissions (called [stored access policies][]) that
supersedes whatever authorizations are embedded in the SAS token. This means
that a service SAS key can be completely deactivated by revoking its
authorizations in the stored access policy. If Jane Doe shows up with a signed
service SAS with wide-ranging permissions but its associated stored access
policy says it has no permissions, that SAS key won't allow Jane to do anything.

[stored access policies]: https://learn.microsoft.com/en-us/rest/api/storageservices/define-stored-access-policy

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
after its creation just like with account SAS tokens with stored access
policies. And like with account SAS + stored access policies, stolen user
delegation SAS tokens can be invalidated by revoking the user delegation keys
used to generate them.

[stored access policies]: https://docs.microsoft.com/en-us/rest/api/storageservices/define-stored-access-policy

## Questions

### How are bearer tokens actually authorized?

Although bearer tokens look like a bunch of random characters strung together,
they are actually self-contained, signed tokens that encode things like scopes
(what it does and doesn't allow its bearer to access) and expiration date.  This
information is just encoded as a JSON Web Token (JWT) which makes it look
scrambled.

You can verify this yourself by getting a bearer token using Azure CLI:

    az account get-access-token

Then pasting that token into <https://jwt.ms/>.