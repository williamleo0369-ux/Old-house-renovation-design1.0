<template>
  <div class="placeholder-view">
      <div class="icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c.251.042.505.042.752 0L14.25 2.25c.251-.042.505-.042.752 0m-5.25 0V1.5c0-.414.336-.75.75-.75h3.5c.414 0 .75.336.75.75v1.604m-4.5 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0m-7.5 5.25h15m-15 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0M3 10.5v5.714c0 .828.672 1.5 1.5 1.5h3.5c.828 0 1.5-.672 1.5-1.5V10.5m-6 0c-.251.042-.505.042-.752 0m0 0c-.251.042-.505.042-.752 0m15-5.25h-15m15 0c.251.042.505.042.752 0m0 0c.251.042.505.042.752 0M21 10.5v5.714c0 .828-.672 1.5-1.5 1.5h-3.5c-.828 0-1.5-.672-1.5-1.5V10.5m6 0c.251.042.505.042.752 0m0 0c.251.042.505.042.752 0" />
        </svg>
    </div>
    <h3>功能开发中</h3>
    <p>我们正在努力开发此功能，敬请期待！</p>
  </div>
</template>

<style scoped>
.placeholder-view {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    flex-direction: column;
    text-align: center;
}
.placeholder-view .icon {
    width: 80px;
    height: 80px;
    color: #d1d5db;
    margin-bottom: 20px;
}
.placeholder-view h3 {
    font-size: 24px;
    color: var(--text-color);
    margin: 0;
}
.placeholder-view p {
    font-size: 16px;
    color: var(--text-color-secondary);
}
</style>