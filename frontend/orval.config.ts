import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: './openapi.json',
    output: {
      target: './src/api/generated.ts',
      client: 'axios',
      override: {
        mutator: {
          path: './src/api/axiosInstance.ts',
          name: 'axiosInstance',
        },
      },
    },
  },
});
