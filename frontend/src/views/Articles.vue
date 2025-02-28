<template>
  <div class="articles">
    <h1>Articles</h1>
    
    <div class="card mb-4">
      <div class="card-body">
        <h5 class="card-title">Filter Articles</h5>
        <div class="row">
          <div class="col-md-4">
            <div class="mb-3">
              <label for="search" class="form-label">Search</label>
              <input type="text" class="form-control" id="search" v-model="searchQuery" placeholder="Search by title...">
            </div>
          </div>
          <div class="col-md-4">
            <div class="mb-3">
              <label for="filter" class="form-label">Filter</label>
              <select class="form-select" id="filter" v-model="filter">
                <option value="all">All Articles</option>
                <option value="with-comments">With Comments</option>
                <option value="gathered">Comments Gathered</option>
                <option value="analyzed">Comments Analyzed</option>
              </select>
            </div>
          </div>
          <div class="col-md-4">
            <div class="mb-3">
              <label for="page-size" class="form-label">Articles Per Page</label>
              <select class="form-select" id="page-size" v-model="pageSize">
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
        </div>
        <div class="d-flex justify-content-end">
          <button class="btn btn-primary" @click="applyFilters">Apply Filters</button>
        </div>
      </div>
    </div>
    
    <article-list 
      ref="articleList"
      :limit="pageSize" 
      :search-query="appliedSearchQuery" 
      :filter="appliedFilter" 
    />
    
    <div class="mt-4">
      <router-link to="/" class="btn btn-secondary">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<script>
import ArticleList from '@/components/ArticleList.vue';

export default {
  name: 'ArticlesView',
  components: {
    ArticleList
  },
  data() {
    return {
      searchQuery: '',
      filter: 'all',
      pageSize: 25,
      appliedSearchQuery: '',
      appliedFilter: 'all'
    }
  },
  methods: {
    applyFilters() {
      // Apply the current filter values
      this.appliedSearchQuery = this.searchQuery;
      this.appliedFilter = this.filter;
      
      // Force the article list to refresh
      if (this.$refs.articleList) {
        this.$refs.articleList.fetchArticles();
      }
    }
  },
  mounted() {
    // Apply filters on initial load
    this.applyFilters();
  }
}
</script>

<style scoped>
.articles {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>
