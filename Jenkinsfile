pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  hostAliases:
  - ip: "192.168.20.250"
    hostnames:
    - "sonarqube.imcc.com"
    - "nexus.imcc.com"
    - "jenkins.imcc.com"
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
        SONAR_URL = 'http://sonarqube.imcc.com:9000'
        SONAR_USER = 'student'
        SONAR_PASS = 'Imccstudent@2025'
        
        // Nexus Configuration
        NEXUS_HOST = 'nexus.imcc.com:8081'
        NEXUS_USER = 'student'
        NEXUS_PASS = 'Imcc@2025'
        
        // Image Configuration
        // Matches deployment.yaml: nexus.imcc.com:8081/signature-forgery-repo/signature-forgery-app
        NEXUS_REPO = 'signature-forgery-repo' 
        IMAGE_NAME = 'signature-forgery-app'
        FULL_IMAGE_NAME = "${NEXUS_HOST}/${NEXUS_REPO}/${IMAGE_NAME}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    container('sonar-scanner') {
                        sh """
                            echo "--- 🔍 Starting Code Analysis ---"
                            sonar-scanner \
                                -Dsonar.projectKey=signature-forgery-detection \
                                -Dsonar.host.url=${SONAR_URL} \
                                -Dsonar.login=${SONAR_USER} \
                                -Dsonar.password=${SONAR_PASS} \
                                -Dsonar.sources=.
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                container('dind') {
                    script {
                        sh """
                            echo "--- 🐳 Waiting for Docker Daemon ---"
                            while ! docker info > /dev/null 2>&1; do
                                echo "Waiting for Docker daemon..."
                                sleep 1
                            done
                            
                            echo "--- 🔨 Building Image ---"
                            docker build -t ${FULL_IMAGE_NAME}:${env.BUILD_ID} .
                            docker tag ${FULL_IMAGE_NAME}:${env.BUILD_ID} ${FULL_IMAGE_NAME}:latest
                            echo "--- ✅ Image Built ---"
                        """
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                container('dind') {
                    script {
                        sh """
                            echo "--- � Logging into Nexus ---"
                            docker login ${NEXUS_HOST} -u ${NEXUS_USER} -p ${NEXUS_PASS}
                            
                            echo "--- 🚀 Pushing Image ---"
                            docker push ${FULL_IMAGE_NAME}:${env.BUILD_ID}
                            docker push ${FULL_IMAGE_NAME}:latest
                        """
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                container('kubectl') {
                    script {
                        sh """
                            echo "--- ☸ Deploying to Kubernetes ---"
                            
                            # Create namespace if it doesn't exist
                            kubectl create namespace signature-forgery || true

                            # Apply k8s manifests
                            if [ -d "k8" ]; then
                                kubectl apply -f k8/ -n signature-forgery
                                
                                echo "--- 🔄 Restarting Deployment to pick up new image ---"
                                kubectl rollout restart deployment/signature-forgery-app -n signature-forgery
                            else
                                echo "Error: k8/ directory not found!"
                                exit 1
                            fi
                        """
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
