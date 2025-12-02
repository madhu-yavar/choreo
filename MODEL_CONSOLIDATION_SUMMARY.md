# zGrid Model Consolidation and Migration Project


## Project Overview
This project consolidates all machine learning models used across the zGrid services into a single directory structure and prepares for migration to an Azure DevOps repository for better management and sharing.

## Current Status
1. ✅ Model files identified and cataloged
2. ✅ Consolidated models directory created
3. ✅ Docker Compose configuration updated
4. 📋 Testing plan created
5. 📋 Azure migration plan created

## Directory Structure
```
consolidated_models/
├── pii_service/
│   └── gliner_small-v2.1/
├── tox_service/
│   ├── hub/
│   └── transformers/
├── jail_service/
│   ├── jailbreak-classifier/
│   └── all-MiniLM-L6-v2/
├── policy_service/
│   └── llamaguard-7b-gguf/
├── ban_service/
├── secrets_service/
└── format_service/
```

## Services Updated
- ✅ PII Service: Uses GLiNER model
- ✅ Toxicity Service: Uses Detoxify models
- ✅ Jailbreak Service: Uses jailbreak classifier and similarity models
- ✅ Policy Service: Uses LlamaGuard model
- ℹ️ Ban Service: No ML models (rule-based)
- ℹ️ Secrets Service: No ML models (rule-based)
- ℹ️ Format Service: No ML models (rule-based)

## Next Steps

### 1. Test Locally with Consolidated Models
- [ ] Stop existing services: `docker-compose down`
- [ ] Start services with consolidated models: `docker-compose up --build -d`
- [ ] Run health checks for all services
- [ ] Perform functional testing for each service

### 2. Prepare Azure DevOps Repository
- [ ] Clone Azure DevOps repository
- [ ] Create Models directory
- [ ] Initialize Git LFS
- [ ] Transfer model files

### 3. Update Project to Use Remote Models
- [ ] Modify docker-compose.yml to use remote model paths
- [ ] Test services with remote models

### 4. Document and Share
- [ ] Update project documentation
- [ ] Create README for Azure DevOps Models repository
- [ ] Share with team members

## Files Created
1. `MODEL_INVENTORY.md` - Catalog of all models and how services use them
2. `TESTING_PLAN.md` - Comprehensive testing procedure
3. `AZURE_MIGRATION_PLAN.md` - Step-by-step migration guide

## Model Sizes
- PII Service: 582MB
- Toxicity Service: 418MB
- Jailbreak Service: 1.3GB
- Policy Service: 3.8GB
- **Total: 6.1GB**

## Important Notes
- Git LFS is required for handling large model files
- All services except Ban, Secrets, and Format use ML models
- Environment variables are correctly mapped to the new directory structure
- Volume mappings in docker-compose.yml have been updated