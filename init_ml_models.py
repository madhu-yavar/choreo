#!/usr/bin/env python3
"""
ML Model initialization and verification script for Azure deployment
Ensures Detoxify models are properly loaded and configured
"""

import os
import sys
import json
import time
from pathlib import Path

def verify_model_availability():
    """Verify that Detoxify ML models are available and functional"""

    print("🤖 ML Model Availability Verification")
    print("=" * 50)

    try:
        # Check detoxify import
        print("📦 Checking detoxify import...")
        from detoxify import Detoxify
        print("✅ detoxify imported successfully")

        # Test model loading
        models_to_test = ['original', 'unbiased', 'multilingual']
        available_models = []
        failed_models = []

        for model_name in models_to_test:
            print(f"\n🔄 Testing {model_name} model...")
            try:
                start_time = time.time()
                model = Detoxify(model_name)
                load_time = time.time() - start_time

                # Test prediction
                test_text = "This is a test sentence for model verification"
                prediction = model.predict(test_text)

                print(f"✅ {model_name} model loaded and working ({load_time:.2f}s)")
                print(f"   Prediction keys: {list(prediction.keys())}")
                available_models.append({
                    'name': model_name,
                    'load_time': load_time,
                    'prediction_keys': list(prediction.keys())
                })

            except Exception as e:
                print(f"❌ {model_name} model failed: {e}")
                failed_models.append({
                    'name': model_name,
                    'error': str(e)
                })

        # Generate verification report
        verification_report = {
            'timestamp': time.time(),
            'detoxify_available': True,
            'available_models': available_models,
            'failed_models': failed_models,
            'total_models_tested': len(models_to_test),
            'successful_models': len(available_models)
        }

        print(f"\n📊 Verification Summary:")
        print(f"   Total models tested: {verification_report['total_models_tested']}")
        print(f"   Successful: {verification_report['successful_models']}")
        print(f"   Failed: {len(failed_models)}")

        if verification_report['successful_models'] > 0:
            print("✅ ML Model verification PASSED - At least one model is working")
            return True, verification_report
        else:
            print("❌ ML Model verification FAILED - No models working")
            return False, verification_report

    except ImportError as e:
        print(f"❌ Detoxify import failed: {e}")
        return False, {
            'timestamp': time.time(),
            'detoxify_available': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        return False, {
            'timestamp': time.time(),
            'detoxify_available': True,
            'verification_error': str(e)
        }

def test_hybrid_detection():
    """Test the hybrid ML + pattern detection system"""

    print("\n🧪 Hybrid Detection System Test")
    print("=" * 40)

    try:
        from enhanced_toxicity_model import EnhancedToxicityModel

        # Initialize model
        print("🔄 Initializing Enhanced Toxicity Model...")
        model = EnhancedToxicityModel()

        # Test cases
        test_cases = [
            {
                'text': "This is a clean sentence",
                'expected_toxic': False
            },
            {
                'text': "You are a fucking idiot",
                'expected_toxic': True
            },
            {
                'text': "I will kill your entire family",
                'expected_toxic': True
            },
            {
                'text': "The patient's medical examination showed normal results",
                'expected_toxic': False  # Context-aware should handle this
            }
        ]

        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: \"{test_case['text']}\"")

            # Test prediction
            prediction_result = model.predict_toxicity(test_case['text'])

            is_toxic = prediction_result['is_toxic']
            ml_confidence = prediction_result.get('ml_confidence', 0)
            pattern_confidence = prediction_result.get('pattern_confidence', 0)

            print(f"   Result: {'TOXIC' if is_toxic else 'CLEAN'}")
            print(f"   ML Confidence: {ml_confidence:.3f}")
            print(f"   Pattern Confidence: {pattern_confidence:.3f}")
            print(f"   Features: {prediction_result.get('features', [])}")

            # Check if result matches expectation
            matches_expectation = is_toxic == test_case['expected_toxic']
            status = "✅ PASS" if matches_expectation else "❌ FAIL"
            print(f"   Status: {status}")

            results.append({
                'test': i,
                'text': test_case['text'],
                'expected_toxic': test_case['expected_toxic'],
                'actual_toxic': is_toxic,
                'ml_confidence': ml_confidence,
                'pattern_confidence': pattern_confidence,
                'passed': matches_expectation
            })

        # Calculate success rate
        passed_tests = sum(1 for r in results if r['passed'])
        total_tests = len(results)
        success_rate = passed_tests / total_tests

        print(f"\n📈 Hybrid Detection Test Results:")
        print(f"   Tests passed: {passed_tests}/{total_tests}")
        print(f"   Success rate: {success_rate*100:.1f}%")

        return success_rate >= 0.75, results  # At least 75% success rate

    except Exception as e:
        print(f"❌ Hybrid detection test failed: {e}")
        return False, {'error': str(e)}

def save_verification_report(ml_available, ml_report, hybrid_working, hybrid_results):
    """Save verification report to file"""

    report = {
        'timestamp': time.time(),
        'ml_model_available': ml_available,
        'ml_verification': ml_report,
        'hybrid_detection_working': hybrid_working,
        'hybrid_test_results': hybrid_results,
        'overall_status': 'PASS' if ml_available and hybrid_working else 'FAIL'
    }

    # Save to current directory and /app (for container)
    report_paths = ['./ml_model_verification_report.json', '/app/ml_model_verification_report.json']

    for path in report_paths:
        try:
            with open(path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📄 Report saved to: {path}")
        except Exception as e:
            print(f"⚠️  Could not save report to {path}: {e}")

def main():
    """Main verification function"""

    print("🚀 Enhanced Toxicity Service ML Model Verification")
    print("=" * 60)
    print("This script verifies ML model availability and hybrid detection")
    print("functionality for Azure deployment readiness.")
    print()

    # Step 1: Verify ML model availability
    ml_available, ml_report = verify_model_availability()

    # Step 2: Test hybrid detection system
    hybrid_working, hybrid_results = test_hybrid_detection()

    # Step 3: Save verification report
    save_verification_report(ml_available, ml_report, hybrid_working, hybrid_results)

    # Step 4: Final status
    print("\n" + "=" * 60)
    print("🎯 FINAL VERIFICATION STATUS")
    print("=" * 60)

    if ml_available and hybrid_working:
        print("✅ ALL VERIFICATIONS PASSED")
        print("   - ML models are available and functional")
        print("   - Hybrid detection system is working correctly")
        print("   - Service is ready for Azure deployment")
        return 0
    else:
        print("❌ VERIFICATION FAILED")
        if not ml_available:
            print("   - ML models are not available or functional")
        if not hybrid_working:
            print("   - Hybrid detection system is not working correctly")
        print("   - Service needs fixes before Azure deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())