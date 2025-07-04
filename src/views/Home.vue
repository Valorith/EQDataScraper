<template>
  <div class="redirect-container">
    <div class="redirect-message">
      <h2>Redirecting...</h2>
      <p>Please wait while we redirect you to the new homepage.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  async mounted() {
    // Redirect to the new main page
    await this.$router.replace({ name: 'MainPage' })
  }
}
</script>

<style scoped>
.redirect-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  text-align: center;
}

.redirect-message h2 {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 1rem;
}

.redirect-message p {
  color: rgba(255, 255, 255, 0.7);
}
</style>