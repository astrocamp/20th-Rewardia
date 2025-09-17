import { nodeResolve } from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import terser from '@rollup/plugin-terser';

export default (commandLineArgs) => {
  const isProduction = commandLineArgs.environment === 'production';

  return {
    input: 'src/scripts/app.js',
    output: {
      file: 'public/scripts/app.js',
      format: 'esm',
      sourcemap: !isProduction
    },
    plugins: [
      nodeResolve({
        browser: true,
        preferBuiltins: false
      }),
      commonjs(),
      // 只在生產環境使用壓縮
      isProduction && terser()
    ].filter(Boolean),
    // 監聽模式配置
    watch: {
      clearScreen: false,
      include: 'src/scripts/**'
    }
  };
};