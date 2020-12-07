# A script for converting Obsidian vault to org-roam

This is a script for converting markdown files in Obsidian vault to org-roam files. Since pandoc could not convert md to org *correctly* (as I expected, I mean), I made this script.

I think I will stop this project once the script succeeds conversion fairly well as I expected. So one should falk this repo and tweak some to make it suitable to one's obsidian vault setting.

## How to use

```bash
$ cd /path/to/obsidian_vault_dir/
$ find . -name "*.md" -type f -exec -exec python /path/to/obs2org.py --daily-path daily --asset-path assets {} \;
```
- This script `obs2org.py` creates an org file at the same directory as the original md file..
- `--daily-path` specifies the directory that contains daily-note files.
- `--asset_path` specifies the directory that contains any non-markdown files.

## Known issues

- Some symbols in math formula could be converted from `*foo*` to `/foo/`, since they are wrongly detected as italic letters.
- Link to image (`![foo](bar)`) are not correctly converted to org format (`[[bar][foo]]`).

## Disclaimer

I played around org-mode for very short period, but the appearance of latex preview (both for inline and equation line) is not very satisfactory for me.
And currently I am kind of back to Obsidian...
