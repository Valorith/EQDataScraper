# Use Node.js 18 LTS
FROM node:18-alpine

# Install build dependencies for native modules
RUN apk add --no-cache python3 make g++

# Set working directory
WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package*.json ./

# Clear npm cache and install dependencies
RUN npm cache clean --force && npm ci

# Rebuild native modules for Alpine Linux platform
RUN npm rebuild

# Copy source code
COPY . .

# Build the Vue app
RUN npm run build

# Install serve globally for production
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Start the application
CMD ["serve", "-s", "dist", "-l", "3000"]