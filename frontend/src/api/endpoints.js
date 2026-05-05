import client from './client';

export const api = {
  // System Health
  getHealth: () => client.get('/health'),

  // Entity Resolution
  er: {
    getStats: () => client.get('/er/stats'),
    getReviewQueue: (page = 1, limit = 20) => client.get('/er/review-queue', { params: { page, limit } }),
    submitReview: (pairId, decision, reason, reviewerId) => client.post(`/er/review/${pairId}`, { decision, reason, reviewer_id: reviewerId }),
    lookupUbid: (params) => client.get('/er/ubid/lookup', { params }), // pan, gstin, name, pincode
    getUbidDetail: (ubid) => client.get(`/er/ubid/${ubid}`),
    runPipeline: () => client.post('/er/run-pipeline')
  },

  // Activity Intelligence
  activity: {
    getStats: () => client.get('/activity/stats'),
    getStatus: (ubid) => client.get(`/activity/status/${ubid}`),
    crossDeptQuery: (params) => client.get('/query/cross-department', { params }),
    getReviewQueue: (page = 1, limit = 20) => client.get('/activity/review-queue', { params: { page, limit } }),
    submitOverride: (ubid, status, reason, reviewerId) => client.post(`/activity/override/${ubid}`, { status, reason, reviewer_id: reviewerId }),
    classifyAll: () => client.post('/activity/classify-all')
  },

  // Events
  events: {
    getAttributionQueue: (page = 1, limit = 20) => client.get('/events/attribution-queue', { params: { page, limit } }),
    attributeEvent: (eventId, ubid, reviewerId) => client.post(`/events/attribute/${eventId}`, { ubid, reviewer_id: reviewerId })
  }
};
