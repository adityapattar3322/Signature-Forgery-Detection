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
                script {
                    // Download and run sonar-scanner locally to avoid Docker DNS issues
                    // Using 'jar' to unzip if 'unzip' is not available (jar is always available in Jenkins agent)
                    def scannerVersion = '5.0.1.3006'
                    sh """
                        curl -sSLo sonar-scanner.zip https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${scannerVersion}-linux.zip
                        unzip -o sonar-scanner.zip || jar xf sonar-scanner.zip
                        mv sonar-scanner-${scannerVersion}-linux sonar-scanner
                        chmod +x sonar-scanner/bin/sonar-scanner
                        
                        // Configure sonar-scanner to use the embedded JRE
                        sed -i 's/use_embedded_jre=false/use_embedded_jre=true/g' sonar-scanner/conf/sonar-scanner.properties
                        
                        ./sonar-scanner/bin/sonar-scanner \
                            -Dsonar.projectKey=signature-forgery-detection \
                            -Dsonar.sources=. \
                            -Dsonar.host.url=${SONAR_URL} \
                            -Dsonar.login=${SONAR_USER} \
                            -Dsonar.password=${SONAR_PASS}
                    """
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
                    // 1. Archive source code (run in default agent)
                    // 'zip' was not found, using 'tar' instead which is standard
                    sh "tar -czf ${IMAGE_NAME}-${env.BUILD_ID}-source.tar.gz --exclude='.git' --exclude='venv' ."

                    // 2. Save Docker image to a tar file (run in dind)
                    container('dind') {
                        sh "docker save -o ${IMAGE_NAME}-${env.BUILD_ID}.tar ${IMAGE_NAME}:${env.BUILD_ID}"
                    }
                    
                    // 3. Upload Source Archive to Nexus (run in default agent)
                    sh """
                    curl -v -u ${NEXUS_USER}:${NEXUS_PASS} \
                        --upload-file ${IMAGE_NAME}-${env.BUILD_ID}-source.tar.gz \
                        ${NEXUS_URL}/repository/${NEXUS_REPO}/${IMAGE_NAME}/${env.BUILD_ID}/${IMAGE_NAME}-${env.BUILD_ID}-source.tar.gz
                    """

                    // 4. Upload Docker Image Tar to Nexus (run in default agent)
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
