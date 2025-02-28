<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">OSINT Comments</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav">
            <li class="nav-item">
              <router-link class="nav-link" to="/">Dashboard</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/crawler">Crawler</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/articles">Articles</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/comments">Comments</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/analysis">Analysis</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <div class="container mt-4">
      <router-view/>
    </div>
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

.router-link-exact-active {
  font-weight: bold;
}
</style>
