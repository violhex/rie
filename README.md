# Reddit Image Extractor (RIE) 

Download images from a Reddit post. 
Handles single images, gallery posts, and preview fallbacks. 
Deduplicates by content hash.

# Wallpapers

I've included this script in my wallpaper collection repository as it is great for collecting random images from Reddit.
If you're interested in what I've come across you can take a look here: <https://github.com/violhex/wallpapers>

## Install

Install as a persistent system command via `uv tool`:

```bash
uv tool install git+https://github.com/violhex/rie
```

This exposes `rie` in `~/.local/bin`. Make sure that's on your `PATH`:

```bash
# ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Updating

```bash
uv tool upgrade rie
```

### Uninstall

```bash
uv tool uninstall rie
```

## Usage

```
rie <reddit_url> -o <output_dir> [options]
```

### Options

| Flag | Default | Description |
|---|---|---|
| `-o, --output-dir` | required | Directory to save images (created if absent) |
| `--max-images N` | unlimited | Stop after downloading N images |
| `--delay MS` | 1000 | Milliseconds between requests |
| `--timeout SECONDS` | 15 | HTTP connect+read timeout per request |
| `--max-bytes BYTES` | 26214400 | Max file size per image (25 MB) |
| `-v, --verbose` | off | Enable debug logging |

## Security notes

- Only accepts `https://` Reddit URLs (`reddit.com`, `www.reddit.com`, `old.reddit.com`, `redd.it`)
- Only downloads from known Reddit/Imgur image hosts
- Filenames are always generated locally — remote filenames are never trusted
- Content-Type is validated before writing any bytes to disk
- Downloads are streamed with a hard size cap (default 25 MB)
- Retries only on transient server errors (5xx); rate-limit responses (429) surface immediately

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Bad arguments or configuration error |
| `2` | At least one image failed to download |
