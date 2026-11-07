#!/usr/bin/env bash
# Fixed public releases. No credentials are used. Verify before extraction/execution.
set -euo pipefail
tool_dir="$(mktemp -d "$RUNNER_TEMP/ue-tools.XXXXXX")"
fetch() {
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$1" -o "$tool_dir/$2"
  printf '%s  %s\n' "$3" "$tool_dir/$2" | sha256sum --check --strict
}
fetch https://nodejs.org/dist/v24.22.2/node-v24.22.2-linux-x64.tar.xz node.tar.xz 48cc0e21e048790e54c0cf5749c2725005313d652651c40b7a21feb9697aaf75
tar -xJf "$tool_dir/node.tar.xz" -C "$tool_dir"
export PATH="$tool_dir/node-v24.22.2-linux-x64/bin:$PATH"
echo "$tool_dir/node-v24.22.2-linux-x64/bin" >> "$GITHUB_PATH"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 https://registry.npmjs.org/pnpm/-/pnpm-10.28.0.tgz -o "$tool_dir/pnpm.tgz"
node -e 'const f=require("node:fs"),c=require("node:crypto");if(c.createHash("sha512").update(f.readFileSync(process.argv[1])).digest("base64")!=="Bd9x0UIfITmeBT/eVnzqNNRG+gLHZXFEG/wceVbpjjYwiJgtlARl/TRIDU2QoGaLwSNi+KqIAApk6D0LDke+SA==")process.exit(1)' "$tool_dir/pnpm.tgz"
tar -xzf "$tool_dir/pnpm.tgz" -C "$tool_dir"
mkdir "$tool_dir/bin"
ln -s "$tool_dir/package/bin/pnpm.cjs" "$tool_dir/bin/pnpm"
fetch https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz actionlint.tgz 8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8
tar -xzf "$tool_dir/actionlint.tgz" -C "$tool_dir/bin" actionlint
fetch https://github.com/zizmorcore/zizmor/releases/download/v1.32.0/zizmor-x86_64-unknown-linux-gnu.tar.gz zizmor.tgz bb110cc765eca9cd7efb2e284a956be5974c60027b0970f16397d86208a9957b
tar -xzf "$tool_dir/zizmor.tgz" -C "$tool_dir/bin"
echo "$tool_dir/bin" >> "$GITHUB_PATH"
