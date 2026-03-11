import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class AIProcessor:
    def __init__(self):
        self.test_scenarios = []
    
    def process_documents(self, files_data, urls):
        """Process uploaded documents and URLs to generate test cases"""
        all_content = []
        
        # Process uploaded files
        for file_data in files_data:
            content = self._extract_content(file_data['path'], file_data['type'])
            all_content.append(content)
        
        # Process URLs
        for url in urls:
            content = self._extract_url_content(url)
            all_content.append(content)
        
        # Generate test scenarios and cases
        combined_content = "\n\n".join(all_content)
        return self._generate_test_cases(combined_content)
    
    def _extract_content(self, file_path, file_type):
        """Extract text from uploaded documents"""
        if file_type in ['docx']:
            return self._extract_docx(file_path)
        elif file_type == 'doc':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    content = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
                    if len(content.strip()) > 50:
                        return content
            except:
                pass
            return ""
        elif file_type == 'pdf':
            return self._extract_pdf(file_path)
        elif file_type == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                return ""
        return ""
    
    def _extract_docx(self, file_path):
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except:
            return ""
    
    def _extract_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except:
            return ""
    
    def _extract_url_content(self, url):
        """Extract content from webpage"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(["script", "style", "meta", "noscript"]):
                element.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            return ' '.join(text_content.split())
        except:
            return ""
    
    def _generate_test_cases(self, content):
        """Generate test scenarios and cases based on applicable categories"""
        results = []
        
        # Identify applicable categories from the 9 specified categories
        applicable_categories = self._identify_applicable_categories(content)
        
        # Generate tests only for applicable categories
        features = self._generate_tests_for_applicable_categories(content, applicable_categories)
        
        ts_counter = 1
        tc_counter = 1
        
        for feature in features:
            scenario = {
                'ts_id': f'TS_{ts_counter:02d}',
                'scenario_desc': feature['description'],
                'test_cases': []
            }
            
            for test_case in feature['test_cases']:
                tc = {
                    'tc_id': f'TC_{tc_counter:02d}',
                    'steps': test_case['steps'],
                    'expected': test_case['expected'],
                    'test_data': test_case.get('test_data', ''),
                    'results': '',
                    'defects': '',
                    'comments': ''
                }
                scenario['test_cases'].append(tc)
                tc_counter += 1
            
            results.append(scenario)
            ts_counter += 1
        
        return results
    
    def _identify_applicable_categories(self, content):
        """Analyze requirement and identify applicable test categories from the 9 specified"""
        content_lower = content.lower()
        applicable = {}
        
        # Define keywords for each of the 9 categories
        category_keywords = {
            'functional': ['feature', 'function', 'capability', 'requirement', 'should', 'must', 'can', 'able to', 'allow', 'enable', 'perform', 'execute', 'process'],
            'positive': ['valid', 'correct', 'success', 'accept', 'allow', 'enable', 'successful', 'work', 'complete', 'succeed'],
            'negative': ['invalid', 'error', 'reject', 'deny', 'prevent', 'fail', 'incorrect', 'wrong', 'bad', 'not allowed', 'cannot'],
            'boundary': ['minimum', 'maximum', 'limit', 'range', 'threshold', 'boundary', 'edge', 'min', 'max', 'exceed', 'exceed'],
            'security': ['security', 'encrypt', 'password', 'token', 'authentication', 'authorization', 'secure', 'https', 'ssl', 'injection', 'xss', 'csrf', 'attack', 'vulnerable', 'protect', 'access control'],
            'usability': ['user', 'interface', 'ui', 'responsive', 'mobile', 'desktop', 'tablet', 'keyboard', 'accessibility', 'screen reader', 'ux', 'experience', 'friendly', 'easy', 'navigate'],
            'error_handling': ['error', 'exception', 'fail', 'timeout', 'retry', 'recovery', 'fallback', 'handle', 'catch', 'exception', 'graceful', 'recover'],
            'data_validation': ['email', 'phone', 'date', 'format', 'data', 'validate', 'verify', 'check', 'whitespace', 'trim', 'required', 'field', 'input'],
            'edge_cases': ['concurrent', 'simultaneous', 'duplicate', 'null', 'empty', 'race condition', 'edge case', 'unusual', 'extreme', 'special case']
        }
        
        # Check which categories are applicable
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    applicable[category] = True
                    break
        
        return applicable
    
    def _generate_tests_for_applicable_categories(self, content, applicable_categories):
        """Generate tests only for applicable categories"""
        features = []
        
        # Generate tests for each applicable category in order
        if applicable_categories.get('functional'):
            features.extend(self._generate_functional_tests(content))
        
        if applicable_categories.get('positive'):
            features.extend(self._generate_positive_tests(content))
        
        if applicable_categories.get('negative'):
            features.extend(self._generate_negative_tests(content))
        
        if applicable_categories.get('boundary'):
            features.extend(self._generate_boundary_tests(content))
        
        if applicable_categories.get('security'):
            features.extend(self._generate_security_tests(content))
        
        if applicable_categories.get('usability'):
            features.extend(self._generate_usability_tests(content))
        
        if applicable_categories.get('error_handling'):
            features.extend(self._generate_error_handling_tests(content))
        
        if applicable_categories.get('data_validation'):
            features.extend(self._generate_data_validation_tests(content))
        
        if applicable_categories.get('edge_cases'):
            features.extend(self._generate_edge_case_tests(content))
        
        return features if features else self._generate_generic_tests(content)
    
    def _generate_functional_tests(self, content):
        """Generate Functional Testing scenarios"""
        return [{
            'description': 'Functional Testing - Core Features and Requirements',
            'test_cases': [
                {
                    'steps': '1. Access the application\n2. Navigate to the feature\n3. Execute the primary workflow\n4. Verify all steps complete successfully\n5. Check that the feature works as specified in requirements',
                    'expected': 'Feature functions exactly as per requirements without errors',
                    'test_data': 'Valid test data matching requirements'
                },
                {
                    'steps': '1. Identify all functional requirements\n2. Execute each requirement one by one\n3. Verify each requirement is met\n4. Check for any deviations from specification\n5. Validate complete workflow execution',
                    'expected': 'All functional requirements are successfully implemented and working',
                    'test_data': 'Standard test data'
                },
                {
                    'steps': '1. Test all sub-features and components\n2. Verify each component works independently\n3. Test integration between components\n4. Check data flow between components\n5. Validate end-to-end functionality',
                    'expected': 'All components work correctly both independently and together',
                    'test_data': 'Comprehensive test data'
                }
            ]
        }]
    
    def _generate_positive_tests(self, content):
        """Generate Positive Testing scenarios"""
        return [{
            'description': 'Positive Testing - Valid Inputs and Happy Path',
            'test_cases': [
                {
                    'steps': '1. Prepare valid test data as per requirements\n2. Enter all required information correctly\n3. Execute the operation\n4. Verify successful completion\n5. Check success message and data persistence',
                    'expected': 'System accepts valid inputs and processes them successfully',
                    'test_data': 'Valid, well-formed data matching all requirements'
                },
                {
                    'steps': '1. Follow the happy path workflow\n2. Enter correct information at each step\n3. Verify acceptance at each stage\n4. Check confirmation messages appear\n5. Validate final state matches expected outcome',
                    'expected': 'Happy path workflow completes successfully with all confirmations',
                    'test_data': 'Correct format and valid values'
                },
                {
                    'steps': '1. Test with various valid input combinations\n2. Verify each combination is accepted\n3. Check results are correct for each combination\n4. Validate data is saved properly\n5. Verify no unexpected errors occur',
                    'expected': 'System handles all valid input combinations correctly',
                    'test_data': 'Multiple valid input combinations'
                }
            ]
        }]
    
    def _generate_negative_tests(self, content):
        """Generate Negative Testing scenarios"""
        return [{
            'description': 'Negative Testing - Invalid Inputs and Error Scenarios',
            'test_cases': [
                {
                    'steps': '1. Prepare invalid test data\n2. Attempt operation with invalid inputs\n3. Verify system rejects the input\n4. Check appropriate error message is displayed\n5. Validate data is not saved or processed',
                    'expected': 'System rejects invalid input with appropriate error message',
                    'test_data': 'Invalid or malformed data'
                },
                {
                    'steps': '1. Leave required fields empty\n2. Attempt to submit or proceed\n3. Verify validation errors appear for each empty field\n4. Check error messages are clear and helpful\n5. Verify form/operation is not submitted',
                    'expected': 'System displays validation errors for all missing required fields',
                    'test_data': 'Empty required fields'
                },
                {
                    'steps': '1. Enter incorrect data format (e.g., text in numeric field)\n2. Attempt submission\n3. Verify format validation error appears\n4. Check error message explains the issue\n5. Validate no processing occurs',
                    'expected': 'System validates data format and rejects incorrect formats',
                    'test_data': 'Wrong format data'
                },
                {
                    'steps': '1. Enter data with invalid characters\n2. Attempt submission\n3. Verify rejection with error message\n4. Check system stability\n5. Validate no data corruption',
                    'expected': 'System rejects data with invalid characters',
                    'test_data': 'Data with invalid characters'
                }
            ]
        }]
    
    def _generate_boundary_tests(self, content):
        """Generate Boundary Testing scenarios"""
        return [{
            'description': 'Boundary Testing - Minimum, Maximum, and Edge Values',
            'test_cases': [
                {
                    'steps': '1. Identify minimum allowed value for the field\n2. Enter the minimum value\n3. Submit the form/operation\n4. Verify the system accepts it\n5. Check processing is correct',
                    'expected': 'System accepts and processes minimum boundary value correctly',
                    'test_data': 'Minimum allowed value'
                },
                {
                    'steps': '1. Identify maximum allowed value for the field\n2. Enter the maximum value\n3. Submit the form/operation\n4. Verify the system accepts it\n5. Check processing is correct',
                    'expected': 'System accepts and processes maximum boundary value correctly',
                    'test_data': 'Maximum allowed value'
                },
                {
                    'steps': '1. Enter value just below the minimum allowed\n2. Attempt submission\n3. Verify system rejects it\n4. Check appropriate error message\n5. Validate no processing occurs',
                    'expected': 'System rejects value below minimum boundary',
                    'test_data': 'Value below minimum'
                },
                {
                    'steps': '1. Enter value just above the maximum allowed\n2. Attempt submission\n3. Verify system rejects it\n4. Check appropriate error message\n5. Validate no processing occurs',
                    'expected': 'System rejects value above maximum boundary',
                    'test_data': 'Value above maximum'
                },
                {
                    'steps': '1. Test with zero value if applicable\n2. Test with negative values if applicable\n3. Test with very large numbers\n4. Verify appropriate handling for each\n5. Check error messages are clear',
                    'expected': 'System handles all boundary edge cases appropriately',
                    'test_data': 'Zero, negative, and large values'
                }
            ]
        }]
    
    def _generate_security_tests(self, content):
        """Generate Security Testing scenarios"""
        return [{
            'description': 'Security Testing - Vulnerability Prevention and Protection',
            'test_cases': [
                {
                    'steps': '1. Attempt SQL injection in input field\n2. Submit the form\n3. Verify injection is prevented\n4. Check error handling\n5. Validate no data breach or unauthorized access',
                    'expected': 'System prevents SQL injection attacks',
                    'test_data': "' OR '1'='1 or similar SQL injection payloads"
                },
                {
                    'steps': '1. Attempt XSS attack by entering script tags\n2. Submit the form\n3. Verify script is not executed\n4. Check output is properly escaped\n5. Validate no malicious code execution',
                    'expected': 'System prevents XSS attacks by escaping output',
                    'test_data': '<script>alert("XSS")</script>'
                },
                {
                    'steps': '1. Check if sensitive operations use HTTPS\n2. Verify SSL certificate is valid\n3. Check for sensitive data in URL parameters\n4. Validate encryption is used\n5. Check security headers are present',
                    'expected': 'All sensitive operations use secure HTTPS connection with proper security headers',
                    'test_data': 'Security protocol verification'
                },
                {
                    'steps': '1. Test password field masking\n2. Verify sensitive data is not logged\n3. Check for secure session handling\n4. Verify authentication tokens are secure\n5. Check access control is enforced',
                    'expected': 'Sensitive data is properly protected and access control is enforced',
                    'test_data': 'Sensitive data handling test'
                }
            ]
        }]
    
    def _generate_usability_tests(self, content):
        """Generate Usability Testing scenarios"""
        return [{
            'description': 'Usability Testing - User Interface and User Experience',
            'test_cases': [
                {
                    'steps': '1. Test on desktop browser (1920x1080)\n2. Verify all elements are visible and properly aligned\n3. Test on tablet (iPad size)\n4. Test on mobile (iPhone size)\n5. Verify responsive design works correctly',
                    'expected': 'Application is responsive and displays correctly on all device sizes',
                    'test_data': 'Multiple device sizes and resolutions'
                },
                {
                    'steps': '1. Test keyboard navigation using Tab key\n2. Verify focus moves in logical order\n3. Test Enter key for form submission\n4. Test Escape key for cancellation\n5. Verify all features are keyboard accessible',
                    'expected': 'All features are fully keyboard accessible with logical navigation order',
                    'test_data': 'Keyboard navigation test'
                },
                {
                    'steps': '1. Test with screen reader software\n2. Verify all labels and descriptions are announced\n3. Check ARIA attributes are present\n4. Verify form fields are properly labeled\n5. Check accessibility compliance',
                    'expected': 'Application is accessible to users with disabilities',
                    'test_data': 'Accessibility testing'
                },
                {
                    'steps': '1. Verify UI elements are clearly visible\n2. Check font sizes are readable\n3. Verify color contrast meets standards\n4. Check buttons and links are easily clickable\n5. Verify error messages are clear and helpful',
                    'expected': 'UI is user-friendly with clear, readable elements',
                    'test_data': 'UI clarity and readability test'
                }
            ]
        }]
    
    def _generate_error_handling_tests(self, content):
        """Generate Error Handling scenarios"""
        return [{
            'description': 'Error Handling - System Resilience and Recovery',
            'test_cases': [
                {
                    'steps': '1. Simulate network failure during operation\n2. Attempt to complete the operation\n3. Verify error is detected and caught\n4. Check user-friendly error message is displayed\n5. Validate retry option is available',
                    'expected': 'System handles network errors gracefully with clear message and retry option',
                    'test_data': 'Network disconnection scenario'
                },
                {
                    'steps': '1. Simulate server timeout (30+ seconds)\n2. Attempt operation\n3. Verify timeout is detected\n4. Check appropriate error message\n5. Validate retry mechanism works',
                    'expected': 'System handles timeouts with appropriate error message and recovery option',
                    'test_data': 'Server timeout scenario'
                },
                {
                    'steps': '1. Simulate database connection failure\n2. Attempt operation that requires database\n3. Verify error is handled gracefully\n4. Check error message is user-friendly\n5. Validate no data loss occurs',
                    'expected': 'System handles database errors without data loss',
                    'test_data': 'Database connection failure'
                },
                {
                    'steps': '1. Simulate permission denied error\n2. Attempt unauthorized operation\n3. Verify error is caught\n4. Check appropriate error message\n5. Validate security is maintained',
                    'expected': 'System properly handles permission errors and maintains security',
                    'test_data': 'Unauthorized access attempt'
                }
            ]
        }]
    
    def _generate_data_validation_tests(self, content):
        """Generate Data Validation scenarios"""
        return [{
            'description': 'Data Validation - Input Format and Type Checking',
            'test_cases': [
                {
                    'steps': '1. Enter invalid email format\n2. Attempt submission\n3. Verify validation error appears\n4. Check error message is clear\n5. Validate form is not submitted',
                    'expected': 'System validates email format correctly',
                    'test_data': 'Invalid email: notanemail, test@, @example.com'
                },
                {
                    'steps': '1. Enter invalid phone format\n2. Attempt submission\n3. Verify validation error appears\n4. Check error message explains required format\n5. Validate form is not submitted',
                    'expected': 'System validates phone format correctly',
                    'test_data': 'Invalid phone: abc123, 12345'
                },
                {
                    'steps': '1. Enter invalid date format\n2. Attempt submission\n3. Verify validation error appears\n4. Check error message shows correct format\n5. Validate form is not submitted',
                    'expected': 'System validates date format correctly',
                    'test_data': 'Invalid date: 32/13/2024, 2024-13-01'
                },
                {
                    'steps': '1. Enter data with leading/trailing spaces\n2. Submit the form\n3. Verify spaces are trimmed\n4. Check data is processed correctly\n5. Validate trimmed data is saved',
                    'expected': 'System trims whitespace from input data',
                    'test_data': '  data with spaces  '
                },
                {
                    'steps': '1. Enter special characters in text field\n2. Submit the form\n3. Verify special characters are handled\n4. Check for injection prevention\n5. Validate data is sanitized',
                    'expected': 'System properly validates and sanitizes special characters',
                    'test_data': 'Special characters: @#$%^&*()'
                }
            ]
        }]
    
    def _generate_edge_case_tests(self, content):
        """Generate Edge Cases scenarios"""
        return [{
            'description': 'Edge Cases - Unusual and Extreme Conditions',
            'test_cases': [
                {
                    'steps': '1. Perform operation with null/empty values\n2. Submit the form\n3. Verify system handles null values\n4. Check error or default behavior\n5. Validate system stability',
                    'expected': 'System handles null values appropriately',
                    'test_data': 'Null/None/empty values'
                },
                {
                    'steps': '1. Perform operation with duplicate data\n2. Submit the form\n3. Verify duplicate handling\n4. Check for errors or warnings\n5. Validate data integrity',
                    'expected': 'System handles duplicate data according to business rules',
                    'test_data': 'Duplicate entries'
                },
                {
                    'steps': '1. Perform concurrent/simultaneous operations\n2. Verify race condition handling\n3. Check data consistency\n4. Validate no conflicts occur\n5. Check system stability',
                    'expected': 'System handles concurrent operations without conflicts or data corruption',
                    'test_data': 'Multiple simultaneous requests'
                },
                {
                    'steps': '1. Enter very long string (exceeding max length)\n2. Attempt submission\n3. Verify length validation\n4. Check truncation or error message\n5. Validate system stability',
                    'expected': 'System enforces length limits and handles overflow gracefully',
                    'test_data': 'String exceeding maximum length'
                },
                {
                    'steps': '1. Test with extreme values (very large/small numbers)\n2. Verify system handles them\n3. Check for overflow/underflow\n4. Validate error handling\n5. Check system stability',
                    'expected': 'System handles extreme values appropriately',
                    'test_data': 'Extreme values (very large/small numbers)'
                }
            ]
        }]
    
    def _generate_generic_tests(self, content):
        """Generate generic tests when no specific categories identified"""
        return [{
            'description': 'Functional Testing - Core Features',
            'test_cases': [
                {
                    'steps': '1. Access the application\n2. Navigate to main features\n3. Execute primary workflows\n4. Verify functionality\n5. Check data integrity',
                    'expected': 'All core features work as expected',
                    'test_data': 'Standard test data'
                }
            ]
        }]
