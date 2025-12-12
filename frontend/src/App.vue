<template>
  <div id="app">
    <header class="app-header">
      <h1>AmStar - Amateur Football Platform</h1>
      <p class="subtitle">Organize and manage amateur football matches</p>
    </header>

    <main class="app-main">
      <TeamList />
    </main>

    <footer class="app-footer">
      <p>&copy; 2024 AmStar - Bachelor's Thesis Project</p>
    </footer>
  </div>
</template>

<script>
import TeamList from './components/TeamList.vue'

export default {
  name: 'App',
  components: {
    TeamList
  }
}
</script>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
}

.app-main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #f5f5f5;
  padding: 1.5rem;
  text-align: center;
  color: #666;
  border-top: 1px solid #e0e0e0;
}

/* Responsive design */
@media (max-width: 768px) {
  .app-header h1 {
    font-size: 1.8rem;
  }

  .app-main {
    padding: 1rem;
  }
}
</style>
