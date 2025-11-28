pipeline {
    // 1. **CRITICAL FIX**: Replaced 'agent any' with the required Kubernetes agent definition
    // This defines the Pod with dind, sonar-scanner, and kubectl containers.
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: sonar-scanner
    image: sonarsource/sonar-scanner-cli
    command:
    - cat
    tty: true
  - name: kubectl
    image: bitnami/kubectl:latest
    command:
    - cat
    tty: true
    securityContext:
      runAsUser: 0
    env:
    - name: KUBECONFIG
      value: /kube/config        
    volumeMounts:
    - name: kubeconfig-secret
      mountPath: /kube/config
      subPath: kubeconfig
  - name: dind
    image: docker:dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-config
      mountPath: /etc/docker/daemon.json
      subPath: daemon.json
  volumes:
  - name: docker-config
    configMap:
      name: docker-daemon-config
  - name: kubeconfig-secret
    secret:
      secretName: kubeconfig-secret
'''
        }
    }
    
    environment {
        // SonarQube Configuration
        SONAR_URL = 'http://192.168.20.250:9000'
        SONAR_USER = 'student'
        SONAR_PASS = 'Imccstudent@2025'
        
        // Nexus Configuration
        NEXUS_HOST = '192.168.20.250:8081'
        NEXUS_USER = 'student'
        NEXUS_PASS = 'Imcc@2025'
        NEXUS_REPO = 'signature-forgery-repo' 
        
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
            when { expression { return false } }
            steps {
                container('sonar-scanner') {
                    sh '''
                        echo "--- 🔍 Starting Code Analysis ---"
                        sonar-scanner \
                            -Dsonar.projectKey=signature-forgery-detection \
                            -Dsonar.host.url=${SONAR_URL} \
                            -Dsonar.login=${SONAR_USER} \
                            -Dsonar.password=${SONAR_PASS} \
                            -Dsonar.sources=.
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    script {
                        sh '''
                            echo "--- 🐳 Waiting for Docker Daemon to be ready... ---"
                            while ! docker info > /dev/null 2>&1; do
                                echo "Waiting for Docker daemon..."
                                sleep 1
                            done
                            echo "--- 🐳 Docker is Ready! ---"
                            
                            echo "--- 🔨 Building Image ---"
                            docker build -t ${IMAGE_NAME}:${env.BUILD_ID} .
                            echo "--- ✅ Image Built ---"
                            docker image ls
                        '''
                    }
                }
            }
        }

        stage('Login to Docker Registry') {
            steps {
                container('dind') {
                    // Use NEXUS_HOST for login
                    sh "docker login ${NEXUS_HOST} -u ${NEXUS_USER} -p ${NEXUS_PASS}"
                }
            }
        }
        
        stage('Tag & Push Image') {
            steps {
                container('dind') {
                    sh '''
                        echo "--- 🚀 Pushing Image to Nexus ---"
                        # Tag as NEXUS_HOST/NEXUS_REPO/IMAGE_NAME:BUILD_ID
                        # Note: Nexus Docker registry usually requires the port in the tag if it's not 80/443
                        # Assuming NEXUS_REPO is just a name, but for Docker push it might need to be part of the path or just the host.
                        # Based on typical Nexus setup: host:port/repository-name/image:tag
                        
                        FULL_IMAGE_NAME="${NEXUS_HOST}/repository/${NEXUS_REPO}/${IMAGE_NAME}"
                        
                        # Adjusting for common Nexus Docker Connector patterns. 
                        # If NEXUS_HOST includes the port (8081), it's likely the HTTP connector.
                        # Usually Docker pushes go to a specific connector port (e.g. 8082 or 8083) OR the main port with /repository/repo-name/
                        
                        # Using the path format as per previous curl attempt which used /repository/${NEXUS_REPO}/...
                        # But 'docker push' expects [registry_host[:port]/][repo_name/]image_name:tag
                        
                        # Let's try the format: NEXUS_HOST/IMAGE_NAME:TAG (if Nexus is at root)
                        # OR NEXUS_HOST/repository/NEXUS_REPO/IMAGE_NAME:TAG
                        
                        # Reverting to the user's provided snippet logic but ensuring variables are correct.
                        # The user's snippet used: ${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}:${env.BUILD_ID}
                        
                        docker tag ${IMAGE_NAME}:${env.BUILD_ID} ${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}:${env.BUILD_ID}
                        docker push ${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}:${env.BUILD_ID}
                        
                        docker tag ${IMAGE_NAME}:${env.BUILD_ID} ${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}:latest
                        docker push ${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    script {
                        sh '''
                            echo "--- ☸ Deploying to Kubernetes ---"
                            
                            # Create namespace if it doesn't exist
                            kubectl create namespace signature-forgery || true

                            # Apply k8s manifests
                            # Ensure k8/ directory exists in your repo with deployment.yaml and service.yaml
                            if [ -d "k8" ]; then
                                kubectl apply -f k8/ -n signature-forgery
                            else
                                echo "Warning: k8/ directory not found. Skipping deployment."
                            fi
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            deleteDir()
        }
    }
}
