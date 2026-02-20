const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// 启动 FastAPI 后端
const fastApiProcess = spawn('python3', ['main.py'], {
  cwd: __dirname,
  stdio: 'inherit',
});

// API 代理
app.use('/api', createProxyMiddleware({
  target: 'http://127.0.0.1:8000', // FastAPI 运行的地址
  changeOrigin: true,
}));

// 托管前端静态文件
app.use(express.static(path.join(__dirname, 'dist')));

app.get('/*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

process.on('exit', () => {
  fastApiProcess.kill();
});
