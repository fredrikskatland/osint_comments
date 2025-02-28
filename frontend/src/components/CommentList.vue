<template>
  <div class="comment-list">
    <h3>Comments</h3>
    <div class="filter-controls mb-3">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Filter Comments</h5>
          
          <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" id="flagged-only" v-model="flaggedOnly">
            <label class="form-check-label" for="flagged-only">Show flagged comments only</label>
          </div>
          
          <div class="row">
            <div class="col-md-4">
              <div class="mb-3">
                <label for="aggressive-filter" class="form-label">
                  Aggressive Score ({{ minAggressive * 100 }}%)
                </label>
                <input 
                  type="range" 
                  class="form-range" 
                  id="aggressive-filter" 
                  v-model.number="minAggressive" 
                  min="0" 
                  max="1" 
                  step="0.05"
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <div class="mb-3">
                <label for="hateful-filter" class="form-label">
                  Hateful Score ({{ minHateful * 100 }}%)
                </label>
                <input 
                  type="range" 
                  class="form-range" 
                  id="hateful-filter" 
                  v-model.number="minHateful" 
                  min="0" 
                  max="1" 
                  step="0.05"
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <div class="mb-3">
                <label for="racist-filter" class="form-label">
                  Racist Score ({{ minRacist * 100 }}%)
                </label>
                <input 
                  type="range" 
                  class="form-range" 
                  id="racist-filter" 
                  v-model.number="minRacist" 
                  min="0" 
                  max="1" 
                  step="0.05"
                >
              </div>
            </div>
          </div>
          
          <div class="d-flex justify-content-end">
            <button class="btn btn-secondary me-2" @click="resetFilters">Reset Filters</button>
            <button class="btn btn-primary" @click="applyFilters">Apply Filters</button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <div v-else-if="comments.length === 0" class="alert alert-info">
      No comments found.
    </div>
    <div v-else>
      <div class="comments-container">
        <div v-for="comment in comments" :key="comment.id" class="card mb-3" 
             :class="{ 'border-danger': comment.is_flagged }">
          <div class="card-header d-flex justify-content-between align-items-center">
            <div>
              <strong>Article:</strong> 
              <a :href="`/articles/${comment.article_identifier}`">{{ comment.article_title }}</a>
            </div>
            <div>
              <span class="badge" :class="comment.is_flagged ? 'bg-danger' : 'bg-success'">
                {{ comment.is_flagged ? 'Flagged' : 'Safe' }}
              </span>
            </div>
          </div>
          <div class="card-body">
            <p class="card-text">{{ comment.message }}</p>
            <div v-if="comment.is_analyzed" class="analysis-scores">
              <div class="progress mb-2">
                <div class="progress-bar bg-danger" role="progressbar" 
                     :style="{ width: `${comment.aggressive_score * 100}%` }" 
                     :aria-valuenow="comment.aggressive_score * 100" 
                     aria-valuemin="0" aria-valuemax="100">
                  Aggressive: {{ Math.round(comment.aggressive_score * 100) }}%
                </div>
              </div>
              <div class="progress mb-2">
                <div class="progress-bar bg-warning" role="progressbar" 
                     :style="{ width: `${comment.hateful_score * 100}%` }" 
                     :aria-valuenow="comment.hateful_score * 100" 
                     aria-valuemin="0" aria-valuemax="100">
                  Hateful: {{ Math.round(comment.hateful_score * 100) }}%
                </div>
              </div>
              <div class="progress mb-2">
                <div class="progress-bar bg-dark" role="progressbar" 
                     :style="{ width: `${comment.racist_score * 100}%` }" 
                     :aria-valuenow="comment.racist_score * 100" 
                     aria-valuemin="0" aria-valuemax="100">
                  Racist: {{ Math.round(comment.racist_score * 100) }}%
                </div>
              </div>
              <div v-if="comment.analysis_explanation" class="explanation mt-2">
                <strong>Explanation:</strong> {{ comment.analysis_explanation }}
              </div>
            </div>
          </div>
          <div class="card-footer text-muted">
            Posted on {{ formatDate(comment.created_at) }}
          </div>
        </div>
      </div>
      
      <!-- Pagination -->
      <div class="d-flex justify-content-between align-items-center">
        <div>
          Showing {{ comments.length }} of {{ total }} comments
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
  name: 'CommentList',
  props: {
    articleId: {
      type: String,
      default: null
    },
    limit: {
      type: Number,
      default: 10
    }
  },
  data() {
    return {
      comments: [],
      total: 0,
      currentPage: 1,
      loading: true,
      error: null,
      flaggedOnly: false,
      minAggressive: 0,
      minHateful: 0,
      minRacist: 0,
      // Store the applied filter values separately
      appliedFilters: {
        flaggedOnly: false,
        minAggressive: 0,
        minHateful: 0,
        minRacist: 0
      }
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
  watch: {
    flaggedOnly() {
      this.currentPage = 1;
      this.fetchComments();
    },
    articleId() {
      this.currentPage = 1;
      this.fetchComments();
    }
  },
  mounted() {
    this.fetchComments();
  },
  methods: {
    resetFilters() {
      this.minAggressive = 0;
      this.minHateful = 0;
      this.minRacist = 0;
      this.flaggedOnly = false;
      this.applyFilters();
    },
    
    applyFilters() {
      // Store the current filter values
      this.appliedFilters = {
        flaggedOnly: this.flaggedOnly,
        minAggressive: this.minAggressive,
        minHateful: this.minHateful,
        minRacist: this.minRacist
      };
      
      // Reset to first page and fetch with new filters
      this.currentPage = 1;
      this.fetchComments();
    },
    
    async fetchComments() {
      this.loading = true;
      this.error = null;
      
      try {
        let url = '/api/comments/list';
        
        // If articleId is provided, use the article-specific endpoint
        if (this.articleId) {
          url = `/api/comments/articles/${this.articleId}`;
        } else if (this.appliedFilters.flaggedOnly && !this.articleId) {
          url = '/api/comments/flagged';
        }
        
        // Prepare parameters
        const params = {
          limit: this.limit,
          offset: this.offset
        };
        
        // Add filter parameters
        if (this.articleId) {
          // For article-specific endpoint, we still need to pass the score filters
          if (this.appliedFilters.minAggressive > 0) {
            params.min_aggressive = this.appliedFilters.minAggressive;
          }
          if (this.appliedFilters.minHateful > 0) {
            params.min_hateful = this.appliedFilters.minHateful;
          }
          if (this.appliedFilters.minRacist > 0) {
            params.min_racist = this.appliedFilters.minRacist;
          }
        } else {
          // For general comments endpoint
          params.flagged_only = this.appliedFilters.flaggedOnly;
          
          if (this.appliedFilters.minAggressive > 0) {
            params.min_aggressive = this.appliedFilters.minAggressive;
          }
          if (this.appliedFilters.minHateful > 0) {
            params.min_hateful = this.appliedFilters.minHateful;
          }
          if (this.appliedFilters.minRacist > 0) {
            params.min_racist = this.appliedFilters.minRacist;
          }
        }
        
        const response = await axios.get(url, { params });
        
        if (response.data.status === 'success') {
          this.comments = response.data.comments;
          this.total = response.data.total;
        } else {
          this.error = response.data.message;
        }
      } catch (error) {
        this.error = `Error fetching comments: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'Unknown';
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    changePage(page) {
      if (page < 1 || page > this.totalPages) return;
      this.currentPage = page;
      this.fetchComments();
    }
  }
}
</script>

<style scoped>
.comment-list {
  margin-bottom: 2rem;
}

.comments-container {
  margin-bottom: 1rem;
}

.analysis-scores {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.progress {
  height: 1.5rem;
}

.progress-bar {
  min-width: 2rem;
  text-align: left;
  padding-left: 0.5rem;
}
</style>
