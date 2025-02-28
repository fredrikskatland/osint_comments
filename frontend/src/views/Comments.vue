<template>
  <div class="comments">
    <h1>Comments</h1>
    
    <!-- Gather Comments Form -->
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Gather Comments</h5>
        <form @submit.prevent="gatherComments">
          <div class="mb-3">
            <label for="article-id" class="form-label">Article ID (Optional)</label>
            <input type="text" class="form-control" id="article-id" v-model="articleId">
            <div class="form-text">Identifier for a specific article (leave empty to gather for all articles)</div>
          </div>
          <div class="mb-3">
            <label for="limit" class="form-label">Limit</label>
            <input type="number" class="form-control" id="limit" v-model="limit" min="1">
            <div class="form-text">Maximum number of articles to process (leave empty for all)</div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Gathering...' : 'Gather Comments' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Result Message -->
    <div class="card mt-4" v-if="result">
      <div class="card-body">
        <h5 class="card-title">Result</h5>
        <div class="alert" :class="result.status === 'success' ? 'alert-success' : 'alert-danger'">
          {{ result.message }}
        </div>
        <div v-if="result.params">
          <h6>Parameters:</h6>
          <ul>
            <li v-for="(value, key) in result.params" :key="key">
              {{ key }}: {{ value || 'None' }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Log Stream -->
    <div class="mt-4">
      <log-stream />
    </div>

    <!-- Comments List -->
    <div class="mt-4">
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">Comments</h5>
            <div class="form-inline">
              <label for="comments-per-page" class="me-2">Comments per page:</label>
              <select class="form-select form-select-sm" id="comments-per-page" v-model="commentsPerPage">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      <comment-list :articleId="viewArticleId" :limit="commentsPerPage" />
    </div>

    <div class="mt-4">
      <router-link to="/" class="btn btn-secondary">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import CommentList from '@/components/CommentList.vue';
import LogStream from '@/components/LogStream.vue';

export default {
  name: 'CommentsView',
  components: {
    CommentList,
    LogStream
  },
  data() {
    return {
      articleId: '',
      limit: null,
      isLoading: false,
      result: null,
      error: null,
      viewArticleId: null,
      commentsPerPage: 25
    }
  },
  mounted() {
    // Check if there's an article ID in the route
    if (this.$route.query.articleId) {
      this.viewArticleId = this.$route.query.articleId;
    }
  },
  methods: {
    async gatherComments() {
      this.isLoading = true;
      this.result = null;
      this.error = null;

      try {
        const response = await axios.post('/api/comments/gather', null, {
          params: {
            article_id: this.articleId || undefined,
            limit: this.limit || undefined
          }
        });
        
        this.result = response.data;
        
        // If gathering for a specific article, update the view to show those comments
        if (this.articleId) {
          this.viewArticleId = this.articleId;
        }
      } catch (error) {
        this.error = error.message;
        this.result = {
          status: 'error',
          message: `Error: ${error.message}`
        };
      } finally {
        this.isLoading = false;
      }
    }
  }
}
</script>

<style scoped>
.comments {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>
