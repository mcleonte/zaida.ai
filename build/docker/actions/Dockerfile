# Extend the official Rasa SDK image
FROM rasa/rasa-sdk

# Use subdirectory as working directory
WORKDIR /app

# Copy any additional custom requirements, if necessary (uncomment next line)
COPY requirements.txt .

# Change back to root user to install dependencies
USER root

# Install extra requirements for actions code, if necessary (uncomment next line)
RUN pip install -r requirements.txt

# # Using volumes instead during dev
# Copy actions folder to working directory
# COPY . actions/

# By best practices, don't run the code with root user
USER 1001
