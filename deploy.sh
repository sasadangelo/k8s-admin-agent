#!/bin/bash
set -e

echo "🚀 Deploying K8s Admin Agent to Minikube"
echo "=========================================="

# Check if image exists in minikube
echo ""
echo "🔍 Checking if image exists in minikube..."
if ! minikube image ls | grep -q "k8s-admin-agent:latest"; then
    echo "⚠️  Image not found in minikube. Building and loading..."

    # Build with podman or docker
    if command -v podman &> /dev/null; then
        echo "📦 Building with Podman..."
        podman build -t k8s-admin-agent:latest .
        echo "📥 Saving and loading into minikube..."
        podman save k8s-admin-agent:latest -o k8s-admin-agent.tar
        minikube image load k8s-admin-agent.tar
        rm k8s-admin-agent.tar
    else
        echo "📦 Building with Docker..."
        docker build -t k8s-admin-agent:latest .
        echo "📥 Loading into minikube..."
        minikube image load k8s-admin-agent:latest
    fi
else
    echo "✅ Image already exists in minikube"
fi

# Step 3: Apply Kubernetes manifests
echo ""
echo "☸️  Step 3: Applying Kubernetes manifests..."
kubectl apply -f k8s-deployment.yaml

# Step 4: Wait for deployment to be ready
echo ""
echo "⏳ Step 4: Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/k8s-admin-agent

# Step 5: Get deployment status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Deployment Status:"
kubectl get deployment k8s-admin-agent
echo ""
echo "🔍 Pods:"
kubectl get pods -l app=k8s-admin-agent
echo ""
echo "🌐 Service:"
kubectl get service k8s-admin-agent
echo ""
echo "=========================================="
echo "🎉 K8s Admin Agent is now running!"
echo ""
echo "To view logs:"
echo "  kubectl logs -l app=k8s-admin-agent -f"
echo ""
echo "To register with AgentStack, run:"
echo "  agentstack agent register --url http://k8s-admin-agent:8000"
echo ""

# Made with Bob
