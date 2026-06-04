import { dirname } from "path";
import { fileURLToPath } from "url";

import { FlatCompat } from "@eslint/eslintrc";

// eslint-config-next 15 ships its presets as eslintrc-style configs, so we bridge
// them into flat config with FlatCompat. (create-next-app 16 generates a different,
// v16-only style that is incompatible with eslint-config-next 15.)
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const compat = new FlatCompat({ baseDirectory: __dirname });

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  { ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"] },
];

export default eslintConfig;
