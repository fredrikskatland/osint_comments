<template>
  <div class="crawler">
    <h1>Crawler</h1>
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Crawl Articles</h5>
        <form @submit.prevent="startCrawl">
          <div class="mb-3">
            <label for="months-back" class="form-label">Months Back</label>
            <input type="number" class="form-control" id="months-back" v-model="monthsBack" min="1" max="12">
            <div class="form-text">Number of months to go back from the current month</div>
          </div>
          <div class="mb-3">
            <label for="max-articles" class="form-label">Max Articles</label>
            <input type="number" class="form-control" id="max-articles" v-model="maxArticles" min="1">
            <div class="form-text">Maximum number of articles to process (leave empty for all)</div>
          </div>
          <div class="mb-3 form-check">
            <input type="checkbox" class="form-check-input" id="process-content" v-model="processContent">
            <label class="form-check-label" for="process-content">Process Content</label>
            <div class="form-text">Whether to process article content</div>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Crawling...' : 'Start Crawl' }}
          </button>
        </form>
      </div>
    </div>

    <!-- Log Stream -->
    <div class="mt-4">
      <log-stream />
    </div>

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
              {{ key }}: {{ value }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div class="mt-4">
      <router-link to="/" class="btn btn-secondary">Back to Dashboard</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import LogStream from '@/components/LogStream.vue';

export default {
  name: 'CrawlerView',
  components: {
    LogStream
  },
  data() {
    return {
      monthsBack: 1,
      maxArticles: null,
      processContent: false,
      isLoading: false,
      result: null,
      error: null
    }
  },
  methods: {
    async startCrawl() {
      this.isLoading = true;
      this.result = null;
      this.error = null;

      try {
        const response = await axios.post('/api/crawler/crawl', null, {
          params: {
            months_back: this.monthsBack,
            max_articles: this.maxArticles || undefined,
            process_content: this.processContent
          }
        });
        
        this.result = response.data;
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
.crawler {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
</style>
