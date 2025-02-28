<template>
  <div class="dashboard">
    <h1>OSINT Comments Dashboard</h1>
    
    <!-- Statistics Cards -->
    <div class="stats-container" v-if="stats">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Articles</h5>
          <p class="card-text">Total: {{ stats.article_stats.total_articles }}</p>
          <p class="card-text">With Comments: {{ stats.article_stats.articles_with_comments }}</p>
          <p class="card-text">Comments Gathered: {{ stats.article_stats.comments_gathered }}</p>
          <p class="card-text">Comments Analyzed: {{ stats.article_stats.comments_analyzed }}</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Comments</h5>
          <p class="card-text">Total: {{ stats.comment_stats.total_comments }}</p>
          <p class="card-text">Analyzed: {{ stats.comment_stats.analyzed_comments }}</p>
          <p class="card-text">Flagged: {{ stats.comment_stats.flagged_comments }}</p>
        </div>
      </div>
    </div>
    <div v-else>
      <p>Loading statistics...</p>
    </div>
    
    <!-- Quick Actions -->
    <div class="actions-container">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Quick Actions</h5>
          <div class="btn-group">
            <router-link to="/crawler" class="btn btn-primary">Crawler</router-link>
            <router-link to="/comments" class="btn btn-success">Comments</router-link>
            <router-link to="/analysis" class="btn btn-warning">Analysis</router-link>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Recent Articles -->
    <div class="mt-4">
      <article-list :limit="5" />
    </div>
    
    <!-- Flagged Comments -->
    <div class="mt-4">
      <h2>Flagged Comments</h2>
      <comment-list :limit="5" :flaggedOnly="true" />
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import ArticleList from '@/components/ArticleList.vue';
import CommentList from '@/components/CommentList.vue';

export default {
  name: 'DashboardView',
  components: {
    ArticleList,
    CommentList
  },
  data() {
    return {
      stats: null,
      error: null
    }
  },
  mounted() {
    this.fetchStats();
  },
  methods: {
    async fetchStats() {
      try {
        const response = await axios.get('/api/crawler/stats');
        if (response.data.status === 'success') {
          this.stats = response.data;
        } else {
          this.error = response.data.message;
        }
      } catch (error) {
        this.error = error.message;
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.stats-container {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.card {
  flex: 1;
  margin-bottom: 20px;
}

.actions-container {
  margin-top: 20px;
}

.btn-group {
  display: flex;
  gap: 10px;
}
</style>
