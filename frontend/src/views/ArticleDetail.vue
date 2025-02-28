<template>
  <div class="article-detail">
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <div v-else-if="!article" class="alert alert-warning">
      Article not found.
    </div>
    <div v-else>
      <h1>{{ article.title }}</h1>
      
      <div class="article-meta mb-3">
        <div><strong>Published:</strong> {{ formatDate(article.published_date) }}</div>
        <div v-if="article.author"><strong>Author:</strong> {{ article.author }}</div>
        <div><strong>Comments:</strong> {{ article.comment_count || 0 }}</div>
        <div class="article-badges">
          <span v-if="article.has_comments" class="badge bg-primary me-1">Has Comments</span>
          <span v-if="article.comments_gathered" class="badge bg-success me-1">Comments Gathered</span>
          <span v-if="article.comments_analyzed" class="badge bg-info me-1">Comments Analyzed</span>
        </div>
      </div>
      
      <div class="article-actions mb-4">
        <a :href="article.url" target="_blank" class="btn btn-primary me-2">
          View Original
        </a>
        <button class="btn btn-success me-2" @click="gatherComments">
          Gather Comments
        </button>
        <button class="btn btn-warning me-2" @click="analyzeComments">
          Analyze Comments
        </button>
      </div>
      
      <div class="card mb-4">
        <div class="card-header">
          <h5 class="card-title mb-0">Article Content</h5>
        </div>
        <div class="card-body">
          <div class="article-content" v-if="article.content">
            <p v-for="(paragraph, index) in articleParagraphs" :key="index">
              {{ paragraph }}
            </p>
          </div>
          <div v-else class="alert alert-info">
            No content available for this article.
          </div>
        </div>
      </div>
      
      <div class="comments-section">
        <h2>Comments</h2>
        <comment-list :articleId="articleId" />
      </div>
      
      <div class="mt-4">
        <router-link to="/" class="btn btn-secondary">Back to Dashboard</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import CommentList from '@/components/CommentList.vue';

export default {
  name: 'ArticleDetailView',
  components: {
    CommentList
  },
  props: {
    articleId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      article: null,
      loading: true,
      error: null,
      actionResult: null
    }
  },
  computed: {
    articleParagraphs() {
      if (!this.article || !this.article.content) return [];
      return this.article.content.split('\n').filter(p => p.trim() !== '');
    }
  },
  mounted() {
    this.fetchArticle();
  },
  methods: {
    async fetchArticle() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/api/crawler/articles/${this.articleId}`);
        
        if (response.data.status === 'success') {
          this.article = response.data.article;
        } else {
          this.error = response.data.message;
        }
      } catch (error) {
        this.error = `Error fetching article: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'Unknown';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    async gatherComments() {
      try {
        const response = await axios.post('/api/comments/gather', null, {
          params: { article_id: this.articleId }
        });
        
        alert(response.data.message || 'Started gathering comments');
      } catch (error) {
        alert(`Error: ${error.message}`);
      }
    },
    async analyzeComments() {
      try {
        const response = await axios.post('/api/analysis/analyze', null, {
          params: { article_id: this.articleId }
        });
        
        alert(response.data.message || 'Started analyzing comments');
      } catch (error) {
        alert(`Error: ${error.message}`);
      }
    }
  }
}
</script>

<style scoped>
.article-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.article-meta {
  color: #666;
  margin-bottom: 1rem;
}

.article-badges {
  margin-top: 0.5rem;
}

.article-content {
  line-height: 1.6;
}
</style>
