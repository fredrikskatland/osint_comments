<template>
  <div class="article-list">
    <h3>Articles</h3>
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <div v-else-if="articles.length === 0" class="alert alert-info">
      No articles found.
    </div>
    <div v-else>
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>Title</th>
              <th>Published Date</th>
              <th>Comments</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="article in articles" :key="article.identifier">
              <td>
                <a :href="article.url" target="_blank">{{ article.title }}</a>
              </td>
              <td>{{ formatDate(article.published_date) }}</td>
              <td>{{ article.comment_count || 0 }}</td>
              <td>
                <span v-if="article.comments_gathered" class="badge bg-success">Gathered</span>
                <span v-else class="badge bg-secondary">Not Gathered</span>
                <span v-if="article.comments_analyzed" class="badge bg-info ms-1">Analyzed</span>
              </td>
              <td>
                <div class="btn-group btn-group-sm">
                  <button class="btn btn-outline-primary" @click="viewArticle(article.identifier)">View</button>
                  <button class="btn btn-outline-success" @click="gatherComments(article.identifier)">Gather</button>
                  <button class="btn btn-outline-warning" @click="analyzeComments(article.identifier)">Analyze</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="d-flex justify-content-between align-items-center">
        <div>
          Showing {{ articles.length }} of {{ total }} articles
        </div>
        <nav aria-label="Page navigation">
          <ul class="pagination">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">Previous</a>
            </li>
            <li v-for="page in totalPages" :key="page" class="page-item" :class="{ active: page === currentPage }">
              <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">Next</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ArticleList',
  props: {
    limit: {
      type: Number,
      default: 10
    }
  },
  watch: {
    limit() {
      // When limit changes, reset to first page and refetch
      this.currentPage = 1;
      this.fetchArticles();
    }
  },
  data() {
    return {
      articles: [],
      total: 0,
      currentPage: 1,
      loading: true,
      error: null,
      actionResult: null
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.limit);
    },
    offset() {
      return (this.currentPage - 1) * this.limit;
    }
  },
  mounted() {
    this.fetchArticles();
  },
  methods: {
    async fetchArticles() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`/api/crawler/articles`, {
          params: {
            limit: this.limit,
            offset: this.offset
          }
        });
        
        if (response.data.status === 'success') {
          this.articles = response.data.articles;
          this.total = response.data.total;
        } else {
          this.error = response.data.message;
        }
      } catch (error) {
        this.error = `Error fetching articles: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'Unknown';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    changePage(page) {
      if (page < 1 || page > this.totalPages) return;
      this.currentPage = page;
      this.fetchArticles();
    },
    viewArticle(articleId) {
      // Navigate to article detail view
      this.$router.push(`/articles/${articleId}`);
    },
    async gatherComments(articleId) {
      try {
        const response = await axios.post('/api/comments/gather', null, {
          params: { article_id: articleId }
        });
        
        alert(response.data.message || 'Started gathering comments');
      } catch (error) {
        alert(`Error: ${error.message}`);
      }
    },
    async analyzeComments(articleId) {
      try {
        const response = await axios.post('/api/analysis/analyze', null, {
          params: { article_id: articleId }
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
.article-list {
  margin-bottom: 2rem;
}
</style>
