This is the source for my personal website.  It is compiled using [Hugo][hugo],
for better or for worse, and relies on the `deploy.sh` script included in the
top level to perform various post-html-rendering cleanup.

Testing
--------------------------------------------------------------------------------

For testing during development, ssh into the testing host using the following:

    ssh -L 1313:127.0.0.1:1313 devhost

This will ssh from your local machine into `devhost`, and tunnel a connection to
`127.0.0.1:1313` on `devhost` which you can access by connecting to your local
machine on port 1313.

Deployment
--------------------------------------------------------------------------------

The `deploy.sh` script performs the following

1. Updates the "Last Updated" footer on each webpage based on the last time a
   change to the source file was committed to the git repository
2. Deletes redundant `.html` files left over from Hugo's `uglyURLs` option which
   we use
3. Ensures that pygmentize is installed and available so that code snippet
   shortcodes are not silently left broken in the final html
4. Deploys the website to the deployment host using rsync

[hugo]: https://gohugo.io/ 
