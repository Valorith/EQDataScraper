# Build stage - use full Node.js for building (Railway deployment)
FROM node:18 AS builder

# Set working directory
WORKDIR /app

# Copy package files (package-lock.json excluded via .dockerignore)
COPY package.json ./

# Install dependencies fresh (no package-lock.json for platform compatibility)
RUN npm install

# Copy source code
COPY . .

# Set build-time environment variables
ARG VITE_BACKEND_URL=https://eqdatascraper-backend-production.up.railway.app
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

# Build the Vue app
RUN npm run build

# Production stage - use Alpine for runtime
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built application from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"]