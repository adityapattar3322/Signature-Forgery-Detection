pipeline {
    agent any

    environment {
        // SonarQube Configuration
        SONAR_URL = 'http://sonarqube.imcc.com/'
        SONAR_USER = 'student'
        SONAR_PASS = 'Imccstudent@2025'
        
        // Nexus Configuration
        NEXUS_URL = 'http://nexus.imcc.com/'
        NEXUS_USER = 'student'
        NEXUS_PASS = 'Imcc@2025'
        NEXUS_REPO = 'signature-forgery-repo' // Change this to your actual repository name
        
        // Docker Image Name
        IMAGE_NAME = 'signature-forgery-app'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                container('dind') {
                    script {
                        // Using Docker to run sonar-scanner since it might not be installed on the agent
                        // Mounting the workspace to /usr/src which is the default workdir for this image
                        sh """
                        docker run --rm \
                            --network host \
                            -v "${WORKSPACE}:/usr/src" \
                            sonarsource/sonar-scanner-cli \
                            -Dsonar.projectKey=signature-forgery-detection \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=${SONAR_URL} \
                            -Dsonar.login=${SONAR_USER} \
                            -Dsonar.password=${SONAR_PASS}
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    script {
                        sh "docker build -t ${IMAGE_NAME}:${env.BUILD_ID} ."
                    }
                }
            }
        }

        stage('Publish to Nexus') {
            steps {
                script {
                    // 1. Zip source code (optional, keeping it for completeness)
                    sh "zip -r ${IMAGE_NAME}-${env.BUILD_ID}-source.zip . -x '*.git*' 'venv*'"

                    // 2. Save Docker image to a tar file
                    container('dind') {
                        sh "docker save -o ${IMAGE_NAME}-${env.BUILD_ID}.tar ${IMAGE_NAME}:${env.BUILD_ID}"
                    }
                    
                    // 3. Upload Source Zip to Nexus
                    sh """
                    curl -v -u ${NEXUS_USER}:${NEXUS_PASS} \
                        --upload-file ${IMAGE_NAME}-${env.BUILD_ID}-source.zip \
                        ${NEXUS_URL}/repository/${NEXUS_REPO}/${IMAGE_NAME}/${env.BUILD_ID}/${IMAGE_NAME}-${env.BUILD_ID}-source.zip
                    """

                    // 4. Upload Docker Image Tar to Nexus
                    sh """
                    curl -v -u ${NEXUS_USER}:${NEXUS_PASS} \
                        --upload-file ${IMAGE_NAME}-${env.BUILD_ID}.tar \
                        ${NEXUS_URL}/repository/${NEXUS_REPO}/${IMAGE_NAME}/${env.BUILD_ID}/${IMAGE_NAME}-${env.BUILD_ID}.tar
                    """
                }
            }
        }
        
        stage('Deploy') {
            steps {
                container('dind') {
                    script {
                        // Simple deployment: Stop old container and run new one
                        try {
                            sh "docker stop ${IMAGE_NAME} || true"
                            sh "docker rm ${IMAGE_NAME} || true"
                        } catch (Exception e) {
                            echo "No existing container to stop."
                        }
                        
                        sh """
                        docker run -d \
                            --name ${IMAGE_NAME} \
                            -p 8501:8501 \
                            ${IMAGE_NAME}:${env.BUILD_ID}
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            // cleanWs() was not found, using deleteDir() to clean up the workspace
            deleteDir()
        }
    }
}
