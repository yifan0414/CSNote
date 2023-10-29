[chezmoi - chezmoi](https://www.chezmoi.io/)
# Install

```bash
sudo apt update
sudo apt install snapd
sudo snap install chezmoi --classic
```

# Quick start

## Concepts

Roughly speaking, chezmoi stores the desired state of your dotfiles in the directory `~/.local/share/chezmoi`. When you run `chezmoi apply`, chezmoi calculates the desired contents for each of your dotfiles and then makes the minimum changes required to make your dotfiles match your desired state. chezmoi's concepts are [described more accurately in the reference manual](https://www.chezmoi.io/reference/concepts/).

## Start using chezmoi on your current machine

Assuming that you have already [installed chezmoi](https://www.chezmoi.io/install/), initialize chezmoi with:

```bash
$ chezmoi init
```

This will create a new git local repository in `~/.local/share/chezmoi` where chezmoi will store its source state. By default, chezmoi only modifies files in the working copy.

Manage your first file with chezmoi:

```bash
$ chezmoi add ~/.bashrc
```

This will copy `~/.bashrc` to `~/.local/share/chezmoi/dot_bashrc`.

Edit the source state:

```bash
$ chezmoi edit ~/.bashrc
```

This will open `~/.local/share/chezmoi/dot_bashrc` in your `$EDITOR`. Make some changes and save the file.

>[!important] Hint
>You don't have to use `chezmoi edit` to edit your dotfiles. See [this FAQ entry](https://www.chezmoi.io/user-guide/frequently-asked-questions/usage/#how-do-i-edit-my-dotfiles-with-chezmoi) for more details.


See what changes chezmoi would make:

```bash
$ chezmoi diff
```


Apply the changes:

```bash
$ chezmoi -v apply
```


All chezmoi commands accept the `-v` (verbose) flag to print out exactly what changes they will make to the file system, and the `-n` (dry run) flag to not make any actual changes. The combination `-n` `-v` is very useful if you want to see exactly what changes would be made.

Next, open a shell in the source directory, to commit your changes:

```bash
$ chezmoi cd
$ git add .
$ git commit -m "Initial commit"
```

[Create a new repository on GitHub](https://github.com/new) called `dotfiles` and then push your repo:


```bash
$ git remote add origin https://github.com/$GITHUB_USERNAME/dotfiles.git
$ git branch -M main
$ git push -u origin main
```

>[!important] Hint
>chezmoi can be configured to automatically add, commit, and push changes to your repo.


chezmoi can also be used with [GitLab](https://gitlab.com/), or [BitBucket](https://bitbucket.org/), [Source Hut](https://sr.ht/), or any other git hosting service.

Finally, exit the shell in the source directory to return to where you were:

```bash
$ exit
```

These commands are summarized in this sequence diagram:

![Summary](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/CZuHJg.png)

## Using chezmoi across multiple machines

On a second machine, initialize chezmoi with your dotfiles repo:

```bash
$ chezmoi init https://github.com/$GITHUB_USERNAME/dotfiles.git
```

This will check out the repo and any submodules and optionally create a chezmoi config file for you.

Check what changes that chezmoi will make to your home directory by running:

```bash
$ chezmoi diff
```

If you are happy with the changes that chezmoi will make then run:

```bash
$ chezmoi apply -v
```

If you are not happy with the changes to a file then either edit it with:

```bash
$ chezmoi edit $FILE
```

Or, invoke a merge tool (by default `vimdiff`) to merge changes between the current contents of the file, the file in your working copy, and the computed contents of the file:

```bash
$ chezmoi merge $FILE
```

On any machine, you can pull and apply the latest changes from your repo with:

```bash
$ chezmoi update -v
```

These commands are summarized in this sequence diagram:

![AyQDBE](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/AyQDBE.png)


## Set up a new machine with a single command

You can install your dotfiles on new machine with a single command:

```bash
$ chezmoi init --apply https://github.com/$GITHUB_USERNAME/dotfiles.git
```

If you use GitHub and your dotfiles repo is called `dotfiles` then this can be shortened to:

```bash
$ chezmoi init --apply $GITHUB_USERNAME
```

This command is summarized in this sequence diagram:

![Oo4IRl](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/Oo4IRl.png)

## Next steps

For a full list of commands run:

```bash
$ chezmoi help
```

chezmoi has much more functionality. Good starting points are reading [articles about chezmoi](https://www.chezmoi.io/links/articles-podcasts-and-videos/) adding more dotfiles, and using templates to manage files that vary from machine to machine and retrieve secrets from your password manager. Read the [user guide](https://www.chezmoi.io/user-guide/setup/) to explore.