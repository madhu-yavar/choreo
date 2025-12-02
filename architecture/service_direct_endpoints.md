# zGrid Service Direct Endpoints - FINAL CONFIGURATION

## Verified Working Direct Endpoints

### Policy Service
- **LoadBalancer IP**: `4.157.142.243:8003`
- **Selector**: `app=policy-service-yavar` ✅
- **Pod Labels**: `app=enhanced-policy-service` + `app=policy-service-yavar` (dual-labeled) ✅
- **Capabilities**: Chemical Weaponization, Self-Harm, Harmful Content
- **Status**: ✅ WORKING

### Toxicity Service
- **LoadBalancer IP**: `128.203.71.126:8001` (NOT 172.171.49.238:8001!)
- **Selector**: `app=tox-service-yavar` ✅
- **Pod Labels**: `app=tox-service-yavar` ✅
- **Status**: ✅ WORKING

### Gateway (Internal Path)
- **Gateway IP**: `172.171.49.238:8008`
- **Policy Internal**: `enhanced-policy-service:8003` ✅
- **Toxicity Internal**: `tox-service-yavar:8001` ✅
- **Status**: ✅ WORKING

## Selector Mismatch Prevention Rules

### 1. ALWAYS CHECK BOTH PATHS
- ✅ Internal service path (gateway uses)
- ✅ External LoadBalancer path (direct endpoint)
- ❌ NEVER assume if one works, the other works

### 2. DUAL-LABELING STRATEGY
For enhanced services that replace old ones:
```bash
kubectl label pod <pod-name> app=<old-label> --overwrite
# AND keep app=<new-label> for internal services
```

### 3. VERIFICATION CHECKLIST
```bash
# 1. Check LoadBalancer selector
kubectl describe svc <service-name> | grep "Selector:"

# 2. Check pod labels
kubectl get pods -l <selector> --show-labels

# 3. Check endpoints exist
kubectl get endpoints <service-name>

# 4. Test both paths
curl http://<loadBalancer-ip>:<port>/health
curl -X POST http://<gateway-ip>/validate ...
```

## Service Architecture Map

```
Direct Endpoint Path (External):
├── Policy: 4.157.142.243:8003 → LoadBalancer → enhanced-policy-service-pod (dual-labeled) ✅
├── Toxicity: 128.203.71.126:8001 → LoadBalancer → tox-service-yavar-pod ✅
└── Other services: [verify individually]

Gateway Path (Internal):
├── Gateway: 172.171.49.238:8008
├── Policy: enhanced-policy-service:8003 → enhanced-policy-service-pod ✅
├── Toxicity: tox-service-yavar:8001 → tox-service-yavar-pod ✅
└── Other services: [working as configured]
```

## COMMON MISTAKES TO AVOID

1. ❌ Forgetting to update LoadBalancer selectors
2. ❌ Not dual-labeling enhanced pods
3. ❌ Assuming wrong LoadBalancer IPs
4. ❌ Only testing gateway path, not direct endpoint
5. ❌ Only testing direct endpoint, not gateway path

## RECOVERY PROCEDURES

If selector mismatch occurs:
1. Identify LoadBalancer selector: `kubectl describe svc <service>`
2. Find correct pod: `kubectl get pods -l <actual-label>`
3. Dual-label the pod: `kubectl label pod <pod> app=<selector-label> --overwrite`
4. Verify endpoints: `kubectl get endpoints <service>`
5. Test both paths: LoadBalancer + Gateway

This configuration represents the FINAL, PERMANENT fix for selector mismatch issues.