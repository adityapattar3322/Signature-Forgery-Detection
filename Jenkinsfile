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
                    // Assuming 'sonar-scanner' is in the PATH or configured as a tool.
                    // If configured as a Global Tool in Jenkins, use: def scannerHome = tool 'SonarScanner'
                    // and prepend ${scannerHome}/bin/ to the command.
                    
                    sh """
                    sonar-scanner \
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
                script {
                    sh "docker build -t ${IMAGE_NAME}:${env.BUILD_ID} ."
                }
            }
        }

        stage('Publish to Nexus') {
            steps {
                script {
                    // 1. Zip source code (optional, keeping it for completeness)
                    sh "zip -r ${IMAGE_NAME}-${env.BUILD_ID}-source.zip . -x '*.git*' 'venv*'"

                    // 2. Save Docker image to a tar file
                    sh "docker save -o ${IMAGE_NAME}-${env.BUILD_ID}.tar ${IMAGE_NAME}:${env.BUILD_ID}"
                    
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
    
    post {
        always {
            cleanWs()
        }
    }
}
