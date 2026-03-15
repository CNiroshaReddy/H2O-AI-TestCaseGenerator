import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class AIProcessor:
    def __init__(self):
        self.test_scenarios = []
        self.noise_patterns = [
            r'copyright|©|all rights reserved',
            r'privacy policy|terms of service|contact us|home|blog',
            r'page not found|404|error|sorry',
            r'press.*enter.*skip|open menu|navigation',
            r'search|login|logout|sign up|register',
            r'practice test automation|practice courses',
            r'^[a-z0-9\s]{1,3}$',
            r'please try again after|try again in|wait.*minutes|wait.*hours',
        ]
    
    def process_documents(self, files_data, urls):
        """Process documents and generate requirement-driven test cases"""
        all_content = []
        
        for file_data in files_data:
            content = self._extract_content(file_data['path'], file_data['type'])
            all_content.append(content)
        
        for url in urls:
            content = self._extract_url_content(url)
            all_content.append(content)
        
        combined_content = "\n\n".join(filter(None, all_content))
        if not combined_content.strip():
            raise ValueError('Could not extract any content from the provided files or URLs. Please check your inputs and try again.')
        return self._generate_test_cases(combined_content)
    
    def _extract_content(self, file_path, file_type):
        """Extract text from documents"""
        if file_type in ['docx']:
            return self._extract_docx(file_path)
        elif file_type == 'doc':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    content = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
                    return content if len(content.strip()) > 50 else ""
            except:
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
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except:
            return ""
    
    def _extract_pdf(self, file_path):
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
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(["script", "style", "meta", "noscript", "footer", "nav"]):
                element.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            return ' '.join(text_content.split())
        except:
            return ""
    
    def _is_noise(self, text):
        """Check if text is likely noise/boilerplate"""
        text_lower = text.lower()
        for pattern in self.noise_patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _extract_requirements(self, content):
        """Extract requirements from content with improved filtering"""
        requirements = []
        
        content = re.sub(r'System Name:.*?\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Functional Requirements\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Non-Functional Requirements\n', '', content, flags=re.IGNORECASE)
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('·') or re.match(r'^\d+[\.\)]\s', line)):
                req = re.sub(r'^[•\-*·\d+\.\)]\s*', '', line).strip()
                if len(req) > 15 and not self._is_noise(req):
                    requirements.append(req)
        
        if not requirements:
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and sentence and not self._is_noise(sentence):
                    requirements.append(sentence)
        
        return requirements
    
    def _generate_test_cases(self, content):
        """Generate test cases from requirements"""
        requirements = self._extract_requirements(content)
        
        if not requirements:
            return self._generate_default_tests()
        
        results = []
        ts_counter = 1
        tc_counter = 1
        
        for req in requirements:
            scenario_obj = {
                'ts_id': f'TS_{ts_counter:02d}',
                'scenario_desc': req,
                'test_cases': []
            }
            
            test_cases = self._create_test_cases_for_requirement(req)
            
            for test_case in test_cases:
                tc = {
                    'tc_id': f'TC_{tc_counter:02d}',
                    'steps': test_case['steps'],
                    'expected': test_case['expected'],
                    'test_data': test_case['test_data'],
                    'results': '',
                    'defects': '',
                    'comments': f"Type: {test_case['type']} | Priority: {test_case['priority']}"
                }
                scenario_obj['test_cases'].append(tc)
                tc_counter += 1
            
            results.append(scenario_obj)
            ts_counter += 1
        
        return results
    
    def _create_test_cases_for_requirement(self, req):
        """Create contextual test cases based on requirement characteristics"""
        req_lower = req.lower()
        test_cases = []
        
        numbers = re.findall(r'\d+', req)
        messages = re.findall(r'"([^"]*)"', req)
        
        test_types = self._determine_test_types(req_lower, numbers, messages)
        
        for test_type in test_types:
            test_case = self._generate_contextual_test_case(test_type, req, req_lower, numbers, messages)
            if test_case['steps']:
                test_cases.append(test_case)
        
        return test_cases
    
    def _determine_test_types(self, req_lower, numbers, messages):
        """Determine which test types are relevant for this requirement"""
        test_types = ['Positive', 'Negative']
        
        if any(keyword in req_lower for keyword in ['email', 'password', 'username', 'phone', 'date', 'format', 'validate', 'required', 'field', 'input', 'must', 'should contain', 'must contain']):
            test_types.append('Validation')
        
        if any(keyword in req_lower for keyword in ['secure', 'encrypt', 'token', 'auth', 'permission', 'access', 'role', 'login', 'password']):
            test_types.append('Security')
        
        if any(keyword in req_lower for keyword in ['lock', 'attempt', 'fail', 'retry', 'timeout', 'session', 'invalid', 'error']):
            test_types.append('Functional')
        
        if any(keyword in req_lower for keyword in ['unique', 'duplicate', 'special', 'character', 'unicode', 'null', 'empty']):
            test_types.append('Edge Case')
        
        if messages or any(keyword in req_lower for keyword in ['message', 'display', 'show', 'notify', 'alert', 'error', 'text']):
            test_types.append('Message')
        
        if any(keyword in req_lower for keyword in ['save', 'store', 'persist', 'database', 'data', 'consistency', 'integrity']):
            test_types.append('Data Consistency')
        
        if any(keyword in req_lower for keyword in ['performance', 'speed', 'load', 'concurrent', 'response', 'time']):
            test_types.append('Performance')
        
        if numbers and not any(x in req_lower for x in ['404', '2020', '2024', 'copyright']):
            test_types.append('Boundary')
        
        return test_types
    
    def _generate_contextual_test_case(self, test_type, req, req_lower, numbers, messages):
        """Generate contextual test case based on type and requirement"""
        if test_type == 'Positive':
            return self._generate_positive_test(req, req_lower)
        elif test_type == 'Negative':
            return self._generate_negative_test(req, req_lower)
        elif test_type == 'Boundary':
            return self._generate_boundary_test(req, req_lower, numbers)
        elif test_type == 'Validation':
            return self._generate_validation_test(req, req_lower)
        elif test_type == 'Security':
            return self._generate_security_test(req, req_lower)
        elif test_type == 'Functional':
            return self._generate_functional_test(req, req_lower)
        elif test_type == 'Edge Case':
            return self._generate_edge_case_test(req, req_lower)
        elif test_type == 'Performance':
            return self._generate_performance_test(req, req_lower)
        elif test_type == 'Data Consistency':
            return self._generate_data_consistency_test(req, req_lower)
        elif test_type == 'Message':
            return self._generate_message_test(req, req_lower, messages)
        
        return {'type': test_type, 'priority': 'Medium', 'steps': '', 'expected': '', 'test_data': ''}
    
    def _extract_action_and_entity(self, req_lower):
        """Dynamically extract action verb and entity from requirement"""
        action_verbs = ['add', 'remove', 'delete', 'create', 'update', 'modify', 'edit', 'submit', 'upload', 'download', 'export', 'import', 'search', 'filter', 'sort', 'view', 'display', 'show', 'hide', 'enable', 'disable', 'lock', 'unlock', 'approve', 'reject', 'publish', 'unpublish']
        
        action = None
        for verb in action_verbs:
            if verb in req_lower:
                action = verb
                break
        
        entity_patterns = [
            r'(?:add|remove|delete|create|update)\s+(?:a\s+)?(\w+)',
            r'(?:users?|items?|products?|records?|entries?|documents?|files?|messages?|comments?|posts?|tasks?|events?|orders?|invoices?|reports?|accounts?|profiles?|settings?|permissions?|roles?|groups?|categories?|tags?|attachments?|notifications?|alerts?|logs?|backups?|versions?|templates?|workflows?|processes?|services?|resources?|assets?|data|information)',
        ]
        
        entity = None
        for pattern in entity_patterns:
            match = re.search(pattern, req_lower)
            if match:
                entity = match.group(1) if match.groups() else match.group(0)
                break
        
        return action, entity
    
    def _generate_positive_test(self, req, req_lower):
        action, entity = self._extract_action_and_entity(req_lower)
        test_data = self._generate_realistic_test_data(req_lower, 'valid')
        
        if action and entity:
            steps = f'1. Prepare valid {entity}: {test_data}\n2. {action.capitalize()} the {entity}\n3. Verify system accepts input\n4. Confirm operation succeeds\n5. Validate {entity} is {action}ed'
            expected = f'System successfully {action}s the {entity}'
        else:
            steps = f'1. Prepare valid test data: {test_data}\n2. Execute the required operation\n3. Verify system accepts input\n4. Confirm operation succeeds\n5. Validate expected outcome'
            expected = 'System successfully executes the required operation'
        
        return {
            'type': 'Positive',
            'priority': 'High',
            'steps': steps,
            'expected': expected,
            'test_data': test_data
        }
    
    def _generate_negative_test(self, req, req_lower):
        action, entity = self._extract_action_and_entity(req_lower)
        test_data = self._generate_realistic_test_data(req_lower, 'invalid')
        
        if action and entity:
            steps = f'1. Prepare invalid {entity}: {test_data}\n2. Attempt to {action} the {entity}\n3. Verify system rejects input\n4. Confirm error message displayed\n5. Verify operation not executed'
            expected = f'System rejects invalid {entity} with appropriate error message'
        else:
            steps = f'1. Prepare invalid test data: {test_data}\n2. Attempt to execute the required operation\n3. Verify system rejects input\n4. Confirm error message displayed\n5. Verify operation not executed'
            expected = 'System rejects invalid input with appropriate error message'
        
        return {
            'type': 'Negative',
            'priority': 'High',
            'steps': steps,
            'expected': expected,
            'test_data': test_data
        }
    
    def _generate_boundary_test(self, req, req_lower, numbers):
        if not numbers:
            return {'type': 'Boundary', 'priority': 'Medium', 'steps': '', 'expected': '', 'test_data': ''}
        
        limit = int(numbers[0])
        
        unit = 'items'
        if 'character' in req_lower or 'char' in req_lower:
            unit = 'characters'
        elif 'hour' in req_lower:
            unit = 'hours'
        elif 'minute' in req_lower:
            unit = 'minutes'
        elif 'second' in req_lower:
            unit = 'seconds'
        elif 'day' in req_lower:
            unit = 'days'
        
        return {
            'type': 'Boundary',
            'priority': 'High',
            'steps': f'1. Test with value at limit: {limit} {unit}\n2. Verify system accepts\n3. Test with value exceeding limit: {limit + 1} {unit}\n4. Verify system rejects\n5. Confirm boundary enforced correctly',
            'expected': f'System enforces limit of {limit} {unit} correctly',
            'test_data': f'At limit: {limit} {unit}, Exceeds limit: {limit + 1} {unit}, Below limit: {max(1, limit - 1)} {unit}'
        }
    
    def _generate_validation_test(self, req, req_lower):
        if 'email' in req_lower:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter invalid email: "user@invalid", "user@.com", "user.com"\n2. Verify validation error\n3. Enter valid email: "user@example.com"\n4. Verify system accepts\n5. Confirm email validation enforced',
                'expected': 'Email format validation properly enforced',
                'test_data': 'Invalid: user@invalid, user@.com, user.com | Valid: user@example.com, test@domain.co.uk'
            }
        elif 'username' in req_lower:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter invalid username: "", "a", "user@123!"\n2. Verify validation error\n3. Enter valid username: "student", "testuser"\n4. Verify system accepts\n5. Confirm username validation enforced',
                'expected': 'Username validation properly enforced',
                'test_data': 'Invalid: empty, single char, special chars | Valid: student, testuser, john_doe'
            }
        elif 'password' in req_lower:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter weak password: "pass123"\n2. Verify validation error\n3. Enter strong password: "SecurePass123!"\n4. Verify system accepts\n5. Confirm password validation enforced',
                'expected': 'Password validation properly enforced',
                'test_data': 'Weak: pass123, PASSWORD123 | Strong: SecurePass123!, MyP@ssw0rd'
            }
        elif 'phone' in req_lower:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter invalid phone: "123", "abc1234567"\n2. Verify validation error\n3. Enter valid phone: "555-123-4567"\n4. Verify system accepts\n5. Confirm phone validation enforced',
                'expected': 'Phone format validation properly enforced',
                'test_data': 'Invalid: 123, abc1234567 | Valid: 555-123-4567, (555) 123-4567'
            }
        elif 'date' in req_lower:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter invalid date: "13/32/2024", "2024-13-01"\n2. Verify validation error\n3. Enter valid date: "12/25/2024"\n4. Verify system accepts\n5. Confirm date validation enforced',
                'expected': 'Date format validation properly enforced',
                'test_data': 'Invalid: 13/32/2024, 2024-13-01 | Valid: 12/25/2024, 2024-12-25'
            }
        else:
            return {
                'type': 'Validation',
                'priority': 'High',
                'steps': '1. Enter invalid data format\n2. Verify validation error\n3. Enter valid data format\n4. Verify system accepts\n5. Confirm validation enforced',
                'expected': 'Data validation properly enforced',
                'test_data': 'Invalid and valid data formats'
            }
    
    def _generate_security_test(self, req, req_lower):
        if 'auth' in req_lower or 'login' in req_lower:
            return {
                'type': 'Security',
                'priority': 'High',
                'steps': '1. Attempt SQL injection: "admin\' OR \'1\'=\'1"\n2. Verify system sanitizes input\n3. Attempt XSS: "<script>alert(\'xss\')</script>"\n4. Verify no script execution\n5. Confirm secure authentication',
                'expected': 'System securely handles authentication and malicious input',
                'test_data': 'SQL injection: admin\' OR \'1\'=\'1 | XSS: <script>alert(\'xss\')</script>'
            }
        else:
            return {
                'type': 'Security',
                'priority': 'High',
                'steps': '1. Attempt SQL injection attack\n2. Verify system sanitizes input\n3. Attempt XSS attack\n4. Verify no script execution\n5. Confirm secure handling',
                'expected': 'System securely handles malicious input',
                'test_data': 'SQL injection, XSS, command injection attempts'
            }
    
    def _generate_functional_test(self, req, req_lower):
        action, entity = self._extract_action_and_entity(req_lower)
        
        if 'invalid' in req_lower:
            return {
                'type': 'Functional',
                'priority': 'High',
                'steps': f'1. Prepare invalid {entity or "data"}\n2. Attempt operation\n3. Verify error message displayed\n4. Confirm operation not executed\n5. Verify system state unchanged',
                'expected': f'System displays error for invalid {entity or "data"}',
                'test_data': f'Invalid {entity or "data"}'
            }
        elif action and entity:
            return {
                'type': 'Functional',
                'priority': 'High',
                'steps': f'1. Prepare valid {entity}\n2. {action.capitalize()} the {entity}\n3. Verify {action} operation completes\n4. Confirm {entity} state updated\n5. Validate system response',
                'expected': f'System successfully {action}s {entity}',
                'test_data': f'Valid {entity} for {action} operation'
            }
        else:
            return {
                'type': 'Functional',
                'priority': 'High',
                'steps': '1. Verify requirement functionality\n2. Execute the required operation\n3. Verify all features work as specified\n4. Check system response\n5. Confirm functionality complete',
                'expected': 'System functionality works as specified',
                'test_data': 'Valid data for functional testing'
            }
    
    def _generate_edge_case_test(self, req, req_lower):
        if 'unique' in req_lower or 'duplicate' in req_lower:
            action, entity = self._extract_action_and_entity(req_lower)
            return {
                'type': 'Edge Case',
                'priority': 'High',
                'steps': f'1. Create {entity or "item"} with unique identifier\n2. Attempt to create same {entity or "item"} again\n3. Verify system prevents duplicate\n4. Check error message\n5. Confirm uniqueness enforced',
                'expected': f'System prevents duplicate {entity or "items"}',
                'test_data': f'Duplicate {entity or "item"} attempt with same identifier'
            }
        else:
            return {
                'type': 'Edge Case',
                'priority': 'Medium',
                'steps': '1. Prepare data with special characters: "@#$%^&*()"\n2. Execute operation\n3. Verify system handles special cases\n4. Check for unexpected behavior\n5. Confirm proper handling',
                'expected': 'System handles edge cases correctly',
                'test_data': 'Special characters: @#$%^&*(), Unicode: ñ, é, 中文, Empty values'
            }
    
    def _generate_performance_test(self, req, req_lower):
        return {
            'type': 'Performance',
            'priority': 'Medium',
            'steps': '1. Execute operation and measure response time\n2. Verify response within acceptable time (< 2 seconds)\n3. Test with multiple concurrent requests (10+ users)\n4. Monitor system resources\n5. Confirm performance acceptable',
            'expected': 'Operation completes within acceptable time under normal and load conditions',
            'test_data': 'Performance monitoring: response time, CPU, memory, concurrent users'
        }
    
    def _generate_data_consistency_test(self, req, req_lower):
        action, entity = self._extract_action_and_entity(req_lower)
        return {
            'type': 'Data Consistency',
            'priority': 'High',
            'steps': f'1. Execute operation with {entity or "test"} data\n2. Verify data saved correctly\n3. Retrieve data from system\n4. Compare original and retrieved data\n5. Confirm data consistency maintained',
            'expected': f'{entity or "Data"} remains consistent after operation',
            'test_data': f'Various {entity or "data"} types: strings, numbers, dates, special characters'
        }
    
    def _generate_message_test(self, req, req_lower, messages):
        if messages:
            msg = messages[0]
            return {
                'type': 'Message',
                'priority': 'High',
                'steps': f'1. Trigger condition for message: "{msg}"\n2. Verify exact message displayed\n3. Check message visibility and formatting\n4. Verify message clarity\n5. Confirm message persists appropriately',
                'expected': f'System displays exact message: "{msg}"',
                'test_data': f'Condition to trigger: "{msg}"'
            }
        else:
            return {
                'type': 'Message',
                'priority': 'High',
                'steps': '1. Execute operation\n2. Verify success/error message displayed\n3. Check message visibility and formatting\n4. Verify message clarity\n5. Confirm message appropriate for context',
                'expected': 'System displays appropriate message',
                'test_data': 'Message display test data'
            }
    
    def _generate_realistic_test_data(self, req_lower, data_type):
        """Generate realistic test data based on requirement context"""
        if 'email' in req_lower:
            if data_type == 'valid':
                return 'user@example.com, test@domain.co.uk'
            else:
                return 'invalid@, user@, @example.com, user.com'
        elif 'username' in req_lower:
            if data_type == 'valid':
                return 'student, testuser, john_doe'
            else:
                return 'empty string, single char, special chars (!@#$%)'
        elif 'password' in req_lower:
            if data_type == 'valid':
                return 'Password123, SecurePass123!, MyP@ssw0rd'
            else:
                return 'pass123, PASSWORD, 12345, abc'
        elif 'phone' in req_lower:
            if data_type == 'valid':
                return '555-123-4567, (555) 123-4567, +1-555-123-4567'
            else:
                return '123, abc1234567, 55512, (555)'
        elif 'date' in req_lower:
            if data_type == 'valid':
                return '12/25/2024, 2024-12-25, 25-Dec-2024'
            else:
                return '13/32/2024, 2024-13-01, 32/12/2024'
        elif 'name' in req_lower:
            if data_type == 'valid':
                return 'John Smith, Jane Doe, Robert Johnson'
            else:
                return '123, @#$%, empty string'
        elif 'amount' in req_lower or 'price' in req_lower or 'cost' in req_lower:
            if data_type == 'valid':
                return '100.50, 1000, 0.99'
            else:
                return '-100, abc, 999999999'
        elif 'url' in req_lower or 'link' in req_lower:
            if data_type == 'valid':
                return 'https://example.com, https://test.co.uk'
            else:
                return 'invalid-url, htp://example.com, example'
        elif 'quantity' in req_lower or 'count' in req_lower or 'number' in req_lower:
            if data_type == 'valid':
                return '1, 5, 10'
            else:
                return '0, -1, abc'
        else:
            if data_type == 'valid':
                return 'Valid test data matching requirement specifications'
            else:
                return 'Invalid/missing data that violates requirement'
    
    def _generate_default_tests(self):
        return [
            {
                'ts_id': 'TS_01',
                'scenario_desc': 'Default Test Case',
                'test_cases': [
                    {
                        'tc_id': 'TC_01',
                        'steps': '1. Access application\n2. Verify basic functionality\n3. Check system response\n4. Validate output\n5. Confirm success',
                        'expected': 'System functions as expected',
                        'test_data': 'Standard test data',
                        'results': '',
                        'defects': '',
                        'comments': 'Default test case'
                    }
                ]
            }
        ]
