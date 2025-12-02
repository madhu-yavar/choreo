# Admin endpoints
@app.post("/admin/entities", response_model=AdminPIIResponse)
def add_custom_entities(req: AdminPIIRequest, x_api_key: Optional[str] = Header(default=None), authorization: Optional[str] = Header(default=None)):
    require_admin_key(x_api_key=x_api_key, authorization=authorization)
    
    try:
        # Convert custom entities to dictionary format
        custom_entities_list = []
        custom_placeholders_dict = {}
        custom_thresholds_dict = {}
        
        if req.custom_entities:
            for entity in req.custom_entities:
                entity_dict = {
                    "type": entity.type,
                    "pattern": entity.pattern,
                    "label": entity.label,
                    "description": entity.description
                }
                custom_entities_list.append(entity_dict)
        
        if req.custom_placeholders:
            for placeholder in req.custom_placeholders:
                custom_placeholders_dict[placeholder.entity_type] = placeholder.placeholder
                
        if req.custom_thresholds:
            for threshold in req.custom_thresholds:
                custom_thresholds_dict[threshold.entity_type] = threshold.threshold
        
        # Save custom configurations
        if custom_entities_list:
            custom_config.save_custom_entities(custom_entities_list)
        if custom_placeholders_dict:
            custom_config.save_custom_placeholders(custom_placeholders_dict)
        if custom_thresholds_dict:
            custom_config.save_custom_thresholds(custom_thresholds_dict)
            
        return {
            "status": "success",
            "message": f"Added {len(custom_entities_list)} custom entities, {len(custom_placeholders_dict)} custom placeholders, and {len(custom_thresholds_dict)} custom thresholds"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add custom PII configurations: {str(e)}")

@app.delete("/admin/entities", response_model=AdminPIIResponse)
def clear_custom_entities(x_api_key: Optional[str] = Header(default=None), authorization: Optional[str] = Header(default=None)):
    require_admin_key(x_api_key=x_api_key, authorization=authorization)
    
    try:
        # Clear custom configurations
        custom_config.clear_custom_configs()
        
        return {
            "status": "success",
            "message": "Custom PII configurations cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear custom PII configurations: {str(e)}")

@app.get("/admin/entities")
def get_custom_entities(x_api_key: Optional[str] = Header(default=None), authorization: Optional[str] = Header(default=None)):
    require_admin_key(x_api_key=x_api_key, authorization=authorization)
    
    try:
        # Load current configurations
        custom_entities = custom_config.load_custom_entities()
        custom_placeholders = custom_config.load_custom_placeholders()
        custom_thresholds = custom_config.load_custom_thresholds()
        
        return {
            "custom_entities": custom_entities,
            "custom_placeholders": custom_placeholders,
            "custom_thresholds": custom_thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve custom PII configurations: {str(e)}")