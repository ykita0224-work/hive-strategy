# Managing Two GitHub Accounts on One Mac

Accounts:
- **Personal:** `ykita0224` — `ykita0224@gmail.com`
- **Work:** `ykita0224-work` (the one for this project)

---

## How It Works (The Goal)

Once set up, everything is **automatic based on directory**:

```
~/
└── Experiment/
    ├── any-personal-repo/      ← personal identity (ykita0224), personal SSH key
    └── ade/                    ← work identity kicks in automatically (ykita0224-work)
        └── hive-strategy/      ← work identity, work SSH key, no manual steps
            └── any-sub-repo/   ← still work identity
```

The mechanism: git's `includeIf "gitdir:..."` applies a separate config file for any repo inside a chosen directory. That config sets the identity **and** forces the correct SSH key via `core.sshCommand`. You never need to think about it again.

---

## Current State of Your Machine

Your `~/.ssh/config` already has:

| SSH Host Alias | Key File | GitHub Account |
|---|---|---|
| `github-personal` | `github_ykita0224_rsa` | ykita0224 |
| `github-work1` | `git-ykitaguchi-bi-rsa` | ykitaguchi-bi (old work) |
| `github.com` (default) | `github_ykita0224_rsa` | ykita0224 |

Your global git config: `ykita0224` / `ykita0224@gmail.com`

---

## Step 1 — Create an SSH Key for `ykita0224-work`

```bash
ssh-keygen -t ed25519 -C "ykita0224-work" -f ~/.ssh/github_ykita0224_work
```

- Do NOT overwrite any existing key
- Set a passphrase (recommended)
- Creates `~/.ssh/github_ykita0224_work` (private) and `.pub` (public)

---

## Step 2 — Add the Public Key to GitHub

```bash
pbcopy < ~/.ssh/github_ykita0224_work.pub
```

1. Log into GitHub as `ykita0224-work` (use incognito)
2. **Settings → SSH and GPG keys → New SSH key**
3. Title: `MacBook - hive-strategy`, paste the key → **Add SSH key**

---

## Step 3 — Update `~/.ssh/config`

Add the `github-work` block and `AddKeysToAgent` to the new key.
Your final `~/.ssh/config`:

```
# Personal account
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ykita0224_rsa
    AddKeysToAgent yes
    UseKeychain yes

# Work account — ykita0224-work
Host github-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ykita0224_work
    AddKeysToAgent yes
    UseKeychain yes

# Old work account
Host github-work1
    HostName github.com
    User git
    IdentityFile ~/.ssh/git-ykitaguchi-bi-rsa

# Default (personal)
Host github.com
    User git
    IdentityFile ~/.ssh/github_ykita0224_rsa
    AddKeysToAgent yes
    UseKeychain yes
```

---

## Step 4 — Create `~/.gitconfig-work`

This file holds the work identity and forces the work SSH key for any git operation, regardless of whether the remote URL says `github.com` or `github-work`.

```ini
[user]
    name = ykita0224-work
    email = your-work-email@example.com

[core]
    sshCommand = ssh -i ~/.ssh/github_ykita0224_work -o IdentitiesOnly=yes
```

> `IdentitiesOnly=yes` prevents SSH from trying other loaded keys first.
> Replace `your-work-email@example.com` with your actual work email.

---

## Step 5 — Wire It Into `~/.gitconfig` with `includeIf`

Add this to the **bottom** of your `~/.gitconfig`:

```ini
[includeIf "gitdir:~/Experiment/ade/"]
    path = ~/.gitconfig-work
```

This tells git: *"for any repo whose `.git` directory lives inside `~/Experiment/ade/`, apply `~/.gitconfig-work` on top of global config."*

That's it. No aliases to remember. No per-repo setup commands.

---

## Step 6 — Test the Connection

```bash
# Should say: Hi ykita0224-work!
ssh -T git@github-work

# Should still say: Hi ykita0224!
ssh -T git@github.com
```

---

## Step 7 — Initialize the `hive-strategy` Repo

```bash
cd /Users/yoshi/Experiment/ade/hive-strategy
git init

# Verify identity was picked up automatically
git config user.name   # → ykita0224-work
git config user.email  # → your-work-email@example.com

# Add remote — can use plain github.com because core.sshCommand handles the key
git remote add origin git@github.com:ykita0224-work/hive-strategy.git

# Or use the alias — both work
git remote add origin git@github-work:ykita0224-work/hive-strategy.git
```

---

## Verification — How to Know It's Working

Inside any repo under `~/Experiment/ade/`:
```bash
git config user.name        # ykita0224-work
git config user.email       # work email
git config core.sshCommand  # ssh -i ~/.ssh/github_ykita0224_work ...
```

Inside any other repo:
```bash
git config user.name        # ykita0224
git config user.email       # ykita0224@gmail.com
git config core.sshCommand  # (empty — uses default SSH)
```

---

## The Traps This Setup Eliminates

| Old Trap | Why It No Longer Matters |
|---|---|
| Forgetting to set `git config user.email` per repo | `includeIf` does it automatically |
| Using wrong SSH alias in remote URL | `core.sshCommand` forces the right key regardless of URL |
| New team member clones with `git@github.com:` | Still works — `core.sshCommand` overrides SSH agent selection |
| Rebooting clears SSH agent | `AddKeysToAgent + UseKeychain` re-loads from macOS Keychain |
| Committing as wrong identity | Impossible inside `~/Experiment/ade/` — identity is directory-scoped |

---

## Cleanup — Remove the Old Work Account (`ykitaguchi-bi`)

The `github-work1` alias and its key (`git-ykitaguchi-bi-rsa`) are from an old work account and can be removed.

### 1 — Check No Repos Still Point to It

```bash
# Search for any remote URLs still using github-work1
grep -r "github-work1" ~/Experiment ~/.gitconfig 2>/dev/null
```

If anything shows up, update those remotes first before proceeding.

### 2 — Remove the Key from the Old GitHub Account

1. Log into the `ykitaguchi-bi` GitHub account
2. **Settings → SSH and GPG keys**
3. Find the key matching `git-ykitaguchi-bi-rsa` → **Delete**

### 3 — Remove the Block from `~/.ssh/config`

Delete these lines from `~/.ssh/config`:

```
# Old work account
Host github-work1
    HostName github.com
    User git
    IdentityFile ~/.ssh/git-ykitaguchi-bi-rsa
```

### 4 — Delete the Key Files

```bash
rm ~/.ssh/git-ykitaguchi-bi-rsa
rm ~/.ssh/git-ykitaguchi-bi-rsa.pub
```

### 5 — Remove from SSH Agent (if loaded)

```bash
ssh-add -d ~/.ssh/git-ykitaguchi-bi-rsa 2>/dev/null || true
```

---

## Remaining Manual Step (One Time Only)

If you ever add a **new work repo outside** `~/Experiment/ade/`, either:
- Move it under `~/Experiment/ade/` (recommended — keep all work there), or
- Add another `includeIf` block pointing to the new parent directory

---

## Day-to-Day Reference

```bash
# Clone a work repo — identity is automatic once inside ~/Experiment/ade/
git clone git@github.com:ykita0224-work/some-repo.git ~/Experiment/ade/some-repo

# Clone a personal repo — anywhere outside ~/Experiment/ade/
git clone git@github.com:ykita0224/some-repo.git

# Check active identity in current repo
git config user.name && git config user.email

# Check which SSH key git will use
git config core.sshCommand
```
