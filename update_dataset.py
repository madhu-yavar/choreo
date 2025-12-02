#!/usr/bin/env python3
"""
Update the gibberish training dataset with batches 3, 4, and 5
"""

import json
from datetime import datetime

def update_dataset():
    """Update the complete 200-sample dataset"""

    # Load current dataset
    dataset_path = "/Users/yavar/Documents/CoE/z_grid/gibberish_service/training_data/gibberish_training_dataset.json"
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # New samples to add
    batch_3_samples = [
        {"text": "no cap that was actually insane", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "bet see you at 8", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "lowkey feeling tired rn ngl", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "caught in 4k", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "absolute unit of a dog", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "main character energy", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "finna head out", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "yeet that into the trash", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "big yikes on that one", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "slay queen pop off", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "understood the assignment", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "giving chaotic energy", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "living rent free in my head", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "sheesh that car is clean", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "weird flex but ok", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "got that unspeakable rizz", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "simp behavior honestly", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "touch grass please", "label": "good", "category": "gen_z_slang", "context": "gaming"},
        {"text": "sus impostor syndrome", "label": "good", "category": "gen_z_slang", "context": "gaming"},
        {"text": "periodt", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "its the audacity for me", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "that fit is fire fr fr", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "ngl this collab goes hard", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "highkey want pizza", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "spill the tea", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "sending me", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "im dead skull emoji", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "ratio + L + bozo", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "vibe check passed", "label": "good", "category": "gen_z_slang", "context": "informal"},
        {"text": "goated with the sauce", "label": "good", "category": "gen_z_slang", "context": "social_media"},
        {"text": "hdjskalwow", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "ncbvncbvncbv", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "eirowqpznm", "label": "gibberish", "category": "random_alphanumeric", "context": "gibberish"},
        {"text": ".......,,,,,,", "label": "gibberish", "category": "punctuation_mash", "context": "gibberish"},
        {"text": "jkfdsljkfdsl", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "aoeuidhtns", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "qazwsxedcrfv", "label": "gibberish", "category": "pattern_alphanumeric", "context": "gibberish"},
        {"text": "mznxbcv", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "lkajsdflkjasdf", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "01010101012", "label": "gibberish", "category": "binary_mash", "context": "gibberish"},
        {"text": "tgyhujikolp", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "zaq12wsx", "label": "gibberish", "category": "pattern_alphanumeric", "context": "gibberish"},
        {"text": "plokijuhygt", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "bbbbnnnnmmmm", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "gfdsaewq", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "uyt765r", "label": "gibberish", "category": "random_alphanumeric", "context": "gibberish"},
        {"text": "cxzcxzcxz", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "fajskldf", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "4r5t6y7u", "label": "gibberish", "category": "pattern_alphanumeric", "context": "gibberish"},
        {"text": "nvmcxlks", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"}
    ]

    batch_4_samples = [
        {"text": "Hello, thank you for contacting Acme Corp. How can I assist you today?", "label": "good", "category": "business_sentence", "context": "business"},
        {"text": "Please refer to the API documentation at https://api.example.com/v2/docs for endpoints and examples.", "label": "good", "category": "url", "context": "technical"},
        {"text": "Order ID: SK-84B7-92X (expected delivery: 2025-12-01)", "label": "good", "category": "sku", "context": "technical"},
        {"text": "User UUID: 3fa85f64-5717-4562-b3fc-2c963f66afa6", "label": "good", "category": "uuid", "context": "technical"},
        {"text": "I'll BRB — grabbing coffee, back in 10.", "label": "good", "category": "internet_slang", "context": "informal"},
        {"text": "System version 1.14.0-rc3 deployed to staging.", "label": "good", "category": "version", "context": "technical"},
        {"text": "Timestamp: 2024-07-15T14:23:05Z", "label": "good", "category": "timestamp", "context": "technical"},
        {"text": "Contact: support@company-example.org for further assistance.", "label": "good", "category": "email", "context": "business"},
        {"text": "Password reset link: https://example.com/reset?token=AbC123-XyZ", "label": "good", "category": "url", "context": "technical"},
        {"text": "The build artifact hash is: a3b1c9f7e4d2f0a9b8c7d6e5f4a3b2c1", "label": "good", "category": "technical_id", "context": "system"},
        {"text": "LOL that was unexpected 😂", "label": "good", "category": "internet_slang", "context": "informal"},
        {"text": "Leet example: pwned -> pwn3d; 1337 speak: h4x0r", "label": "good", "category": "leetspeak", "context": "informal"},
        {"text": "Meeting rescheduled to Mon, 2025-01-06 at 09:30 AM IST.", "label": "good", "category": "date_time", "context": "business"},
        {"text": "Device serial: SN-0092-77-ABCD", "label": "good", "category": "technical_id", "context": "technical"},
        {"text": "Please cc: jane.doe@finance.example on the quarterly report.", "label": "good", "category": "email", "context": "business"},
        {"text": "API call example: POST https://example.com/api/v1/users {\"name\":\"Alex\"}", "label": "good", "category": "url", "context": "technical"},
        {"text": "Ref: INV-2025-00047 (paid)", "label": "good", "category": "invoice", "context": "business"},
        {"text": "Client token: tok_live_51HfEw92bZ4q3", "label": "good", "category": "technical_id", "context": "system"},
        {"text": "ETA 00:15:32 (hh:mm:ss)", "label": "good", "category": "timestamp", "context": "technical"},
        {"text": "Reminder: submit Q3 budget spreadsheet by 2025-04-30.", "label": "good", "category": "business_sentence", "context": "business"},
        {"text": "Short link: http://bit.ly/3xYzAbC", "label": "good", "category": "url", "context": "technical"},
        {"text": "Version tag: release-2025_11_01-build-257", "label": "good", "category": "version", "context": "technical"},
        {"text": "SKU: PROD-XL-2025-RED-001", "label": "good", "category": "sku", "context": "technical"},
        {"text": "FYI the server 10.0.3.21 is under maintenance until 02:00 UTC.", "label": "good", "category": "ip_address", "context": "technical"},
        {"text": "User said: \"ttyl, got to run\" in the chat log.", "label": "good", "category": "internet_slang", "context": "informal"},
        {"text": "Checksum (SHA256): e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "label": "good", "category": "technical_id", "context": "system"},
        {"text": "Backup completed at 2025-08-20 03:00:00+05:30", "label": "good", "category": "timestamp", "context": "technical"},
        {"text": "Casual: naw, I can't make it tonight, maybe next week?", "label": "good", "category": "informal_sentence", "context": "informal"},
        {"text": "Endpoint: wss://realtime.example.net/socket/stream", "label": "good", "category": "url", "context": "technical"},
        {"text": "Keyboard mash but meaningful: asdf -> commonly typed sequence in forms", "label": "good", "category": "keyboard_mash_example", "context": "technical"},
        {"text": "asdfghjklqwertyuiopzxcvbnm12345", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "qwertyuiop[]\\asdfghjkl;'zxcvbnm,./", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "lkjhgfdsa987654321mnbvcxz", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "z9x8c7v6b5n4m3l2k1j0h9g8", "label": "gibberish", "category": "random_chars", "context": "gibberish"},
        {"text": "!!!!!@@@@@$$$$$%%%%%^^^^^&&&&&", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "010101001110100100101011000111010001", "label": "gibberish", "category": "binary_noise", "context": "gibberish"},
        {"text": "h3jkl!@#$%^&())_+|}{\":?><", "label": "gibberish", "category": "random_symbols", "context": "gibberish"},
        {"text": "nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn", "label": "gibberish", "category": "repetitive", "context": "gibberish"},
        {"text": "p0w3r^%$#@@!@@@qwe", "label": "gibberish", "category": "mixed_gibberish", "context": "gibberish"},
        {"text": "kl;';/.,mnbvcxzqazwsxedc", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "555-5555-5555-5555-5555", "label": "gibberish", "category": "repetitive_numbers", "context": "gibberish"},
        {"text": "xXxXxXxXxXxXxXxXxXxX", "label": "gibberish", "category": "repetitive_pattern", "context": "gibberish"},
        {"text": "blobblobblobblobblobblob", "label": "gibberish", "category": "random_word_repeat", "context": "gibberish"},
        {"text": "z!z!z!z!z!z!z!z!z!z!", "label": "gibberish", "category": "repetitive_symbols", "context": "gibberish"},
        {"text": "x7G#9qP!sL^z8@r0m", "label": "gibberish", "category": "random_chars", "context": "gibberish"},
        {"text": "randomsequencewithnospacesandmeaning", "label": "gibberish", "category": "random_chars", "context": "gibberish"},
        {"text": "Nm3kL9pQ2sV8tR1yZ0uB", "label": "gibberish", "category": "alphanumeric_noise", "context": "gibberish"},
        {"text": "72f4-72f4-72f4-72f4-72f4", "label": "gibberish", "category": "repetitive_pattern", "context": "gibberish"},
        {"text": "uytrewqpoiuytrewqpoiuyt", "label": "gibberish", "category": "keyboard_mash", "context": "gibberish"},
        {"text": "System log: ERR##@!##$%$#@!--++--", "label": "gibberish", "category": "log_noise", "context": "gibberish"},
        {"text": "w00t! that match was sick lol", "label": "good", "category": "internet_slang", "context": "informal"},
        {"text": "Reference: RFC-7231 Section 4.3.1", "label": "good", "category": "technical_reference", "context": "technical"},
        {"text": "Backup ID: bk_20251101_7f9a3c", "label": "good", "category": "technical_id", "context": "system"},
        {"text": "Happy to help — please see attached file: invoice_Q3_final.pdf", "label": "good", "category": "business_sentence", "context": "business"},
        {"text": "Short chat shorthand: 'gtg, ttyl' from the user log", "label": "good", "category": "internet_slang", "context": "informal"},
        {"text": "API Key (truncated): sk_live_****************abcd", "label": "good", "category": "technical_id", "context": "system"},
        {"text": "Leetspeak: 'elite' -> 3l173", "label": "good", "category": "leetspeak", "context": "informal"}
    ]

    # Combine all new samples
    all_new_samples = batch_3_samples + batch_4_samples

    # Add new samples to existing training_samples
    dataset['training_samples'].extend(all_new_samples)

    # Update metadata
    dataset['metadata']['total_samples'] = len(dataset['training_samples'])
    dataset['metadata']['current_batch'] = 4
    dataset['metadata']['last_updated'] = datetime.now().isoformat()

    # Recalculate category counts
    good_count = sum(1 for s in dataset['training_samples'] if s['label'] == 'good')
    gibberish_count = sum(1 for s in dataset['training_samples'] if s['label'] == 'gibberish')

    dataset['metadata']['categories']['good']['count'] = good_count
    dataset['metadata']['categories']['gibberish']['count'] = gibberish_count

    # Save updated dataset
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ Dataset updated with {len(all_new_samples)} new samples")
    print(f"📊 Total samples: {len(dataset['training_samples'])}")
    print(f"📈 Good samples: {good_count}")
    print(f"🎯 Gibberish samples: {gibberish_count}")

if __name__ == "__main__":
    update_dataset()