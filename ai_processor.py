import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class AIProcessor:
    def __init__(self):
        self.test_scenarios = []
        self.generated_scenarios = set()
    
    def process_documents(self, files_data, urls):
        """Process documents and generate unique requirement-driven test cases"""
        all_content = []
        
        for file_data in files_data:
            content = self._extract_content(file_data['path'], file_data['type'])
            all_content.append(content)
        
        for url in urls:
            content = self._extract_url_content(url)
            all_content.append(content)
        
        combined_content = "\n\n".join(all_content)
        return self._senior_qa_pipeline(combined_content)
    
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
            
            for element in soup(["script", "style", "meta", "noscript"]):
                element.decompose()
            
            text_content = soup.get_text(separator=' ', strip=True)
            return ' '.join(text_content.split())
        except:
            return ""
    
    def _senior_qa_pipeline(self, content):
        """Execute Senior QA Engineer pipeline"""
        requirements = self._extract_requirements(content)
        analysis = self._analyze_requirements(requirements)
        
        results = []
        ts_counter = 1
        tc_counter = 1
        
        for req_idx, (req_id, req_data) in enumerate(analysis.items()):
            scenario_obj = {
                'ts_id': f'TS_{ts_counter:02d}',
                'scenario_desc': req_data['requirement'],
                'test_cases': []
            }
            
            test_cases = self._generate_comprehensive_test_cases(req_data, req_idx)
            
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
        
        return results if results else self._generate_default_tests()
    
    def _extract_requirements(self, content):
        """Extract requirements from ANY format"""
        requirements = []
        
        # Clean headers
        content = re.sub(r'System Name:.*?\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Functional Requirements\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Non-Functional Requirements\n', '', content, flags=re.IGNORECASE)
        
        # Method 1: Bullet/Numbered format
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('·') or re.match(r'^\d+[\.\)]\s', line)):
                req = re.sub(r'^[•\-*·\d+\.\)]\s*', '', line).strip()
                if len(req) > 15:
                    requirements.append(req)
        
        # Method 2: Paragraph format (sentence splitting)
        if not requirements:
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and sentence and not any(x in sentence.lower() for x in ['system name', 'functional', 'requirements']):
                    requirements.append(sentence)
        
        # Method 3: Line-by-line (each non-empty line is a requirement)
        if not requirements:
            for line in lines:
                line = line.strip()
                if len(line) > 20 and line and not any(x in line.lower() for x in ['system name', 'functional', 'requirements']):
                    requirements.append(line)
        
        return requirements
    
    def _analyze_requirements(self, requirements):
        """Analyze requirements and extract components"""
        analysis = {}
        
        for idx, req in enumerate(requirements):
            req_id = f'REQ-{idx+1}'
            analysis[req_id] = {
                'requirement': req,
                'actors': self._extract_actors(req),
                'actions': self._extract_actions(req),
                'entities': self._extract_entities(req),
                'conditions': self._extract_conditions(req),
                'constraints': self._extract_constraints(req),
                'validations': self._extract_validations(req),
                'business_rules': self._extract_business_rules(req),
                'error_scenarios': self._extract_error_scenarios(req),
                'security_concerns': self._extract_security_concerns(req)
            }
        
        return analysis
    
    def _extract_actors(self, req):
        actors = set()
        patterns = ['user', 'admin', 'system', 'application', 'customer', 'guest', 'member']
        for p in patterns:
            if p in req.lower():
                actors.add(p.capitalize())
        return list(actors) if actors else ['User']
    
    def _extract_actions(self, req):
        actions = set()
        patterns = ['create', 'register', 'login', 'logout', 'verify', 'validate', 'lock', 'unlock', 'browse', 'search', 'filter', 'sort', 'add', 'remove', 'update', 'delete', 'edit', 'view', 'display', 'show', 'hide', 'checkout', 'pay', 'purchase', 'generate', 'send', 'receive', 'download', 'upload', 'export', 'import', 'cancel', 'retry', 'reset', 'recover', 'restore', 'backup', 'sync', 'refresh', 'reload', 'submit', 'approve', 'reject', 'confirm', 'deny']
        for p in patterns:
            if p in req.lower():
                actions.add(p)
        return list(actions) if actions else ['execute']
    
    def _extract_entities(self, req):
        entities = set()
        patterns = ['account', 'user', 'email', 'password', 'product', 'cart', 'order', 'payment', 'address', 'event', 'registration', 'ticket', 'seat', 'confirmation', 'form', 'book', 'document', 'file', 'record', 'item', 'data', 'page', 'button', 'field', 'profile', 'dashboard', 'notification', 'message', 'comment', 'review', 'rating', 'category', 'tag', 'filter', 'report', 'invoice', 'receipt', 'transaction', 'session', 'token', 'permission', 'role']
        for p in patterns:
            if p in req.lower():
                entities.add(p)
        return list(entities) if entities else ['item']
    
    def _extract_conditions(self, req):
        conditions = set()
        if 'if' in req.lower() or 'when' in req.lower():
            conditions.add('conditional')
        if 'must' in req.lower() or 'should' in req.lower() or 'required' in req.lower():
            conditions.add('mandatory')
        if 'can' in req.lower() or 'able to' in req.lower() or 'may' in req.lower():
            conditions.add('capability')
        if 'not' in req.lower() or 'cannot' in req.lower() or 'should not' in req.lower():
            conditions.add('restriction')
        if 'before' in req.lower() or 'after' in req.lower() or 'during' in req.lower():
            conditions.add('temporal')
        if 'only' in req.lower() or 'only if' in req.lower():
            conditions.add('exclusive')
        return list(conditions) if conditions else ['standard']
    
    def _extract_constraints(self, req):
        constraints = set()
        if any(x in req.lower() for x in ['maximum', 'max', 'limit', 'exceed', 'more than', 'not more', 'up to']):
            constraints.add('max_limit')
        if any(x in req.lower() for x in ['minimum', 'min', 'at least', 'exactly', 'no less']):
            constraints.add('min_limit')
        if any(x in req.lower() for x in ['length', 'character', 'digit', 'number', 'format', 'valid', 'pattern']):
            constraints.add('format')
        if any(x in req.lower() for x in ['available', 'exist', 'present', 'full', 'empty', 'out of stock', 'unavailable']):
            constraints.add('availability')
        if any(x in req.lower() for x in ['email', 'phone', 'address', 'name', 'payment', 'credit', 'debit']):
            constraints.add('field_validation')
        if any(x in req.lower() for x in ['unique', 'duplicate', 'distinct']):
            constraints.add('uniqueness')
        if any(x in req.lower() for x in ['time', 'minute', 'hour', 'day', 'week', 'month', 'year', 'second', 'duration', 'timeout', 'expir']):
            constraints.add('time_based')
        return list(constraints) if constraints else []
    
    def _extract_validations(self, req):
        validations = set()
        if 'email' in req.lower() and 'valid' in req.lower():
            validations.add('Valid email format')
        if 'unique' in req.lower() and 'email' in req.lower():
            validations.add('Email must be unique')
        if 'password' in req.lower():
            if '8' in req or 'character' in req.lower():
                validations.add('Minimum 8 characters')
            if 'uppercase' in req.lower():
                validations.add('At least one uppercase')
            if 'number' in req.lower() or 'digit' in req.lower():
                validations.add('At least one number')
            if 'special' in req.lower():
                validations.add('At least one special character')
        if 'phone' in req.lower() and '10' in req:
            validations.add('Exactly 10 digits')
        if 'between' in req.lower() and any(x in req.lower() for x in ['1', '5']):
            validations.add('Range validation')
        return list(validations) if validations else []
    
    def _extract_business_rules(self, req):
        rules = set()
        if 'verification' in req.lower() or 'activate' in req.lower() or 'confirm' in req.lower():
            rules.add('Verification required')
        if 'confirmation' in req.lower():
            rules.add('Generate confirmation')
        if 'email' in req.lower() and ('send' in req.lower() or 'receive' in req.lower() or 'notification' in req.lower()):
            rules.add('Send email notification')
        if 'lock' in req.lower():
            rules.add('Account locking')
        if 'out of stock' in req.lower() or 'unavailable' in req.lower():
            rules.add('Check availability')
        if 'payment' in req.lower():
            rules.add('Process payment')
        if 'order' in req.lower():
            rules.add('Generate order')
        if 'cancel' in req.lower():
            rules.add('Cancel operation')
        return list(rules) if rules else []
    
    def _extract_error_scenarios(self, req):
        errors = set()
        if 'invalid' in req.lower():
            errors.add('Invalid input')
        if 'incorrect' in req.lower() or 'wrong' in req.lower():
            errors.add('Incorrect data')
        if 'lock' in req.lower():
            errors.add('Account locked')
        if 'out of stock' in req.lower():
            errors.add('Out of stock')
        if 'payment' in req.lower() and 'fail' in req.lower():
            errors.add('Payment failure')
        if 'empty' in req.lower() or 'required' in req.lower():
            errors.add('Missing required field')
        if 'duplicate' in req.lower():
            errors.add('Duplicate entry')
        if 'not found' in req.lower() or 'does not exist' in req.lower():
            errors.add('Not found')
        return list(errors) if errors else []
    
    def _extract_security_concerns(self, req):
        security = set()
        if 'password' in req.lower():
            security.add('Password security')
        if 'email' in req.lower():
            security.add('Email validation')
        if 'payment' in req.lower() or 'credit' in req.lower():
            security.add('Payment security')
        if 'encrypt' in req.lower() or 'secure' in req.lower():
            security.add('Encryption')
        if 'token' in req.lower() or 'session' in req.lower():
            security.add('Session management')
        if 'permission' in req.lower() or 'access' in req.lower():
            security.add('Access control')
        return list(security) if security else []
    
    def _generate_comprehensive_test_cases(self, req_data, req_idx):
        """Generate 6-10 comprehensive test cases for 75%+ coverage"""
        req = req_data['requirement']
        test_cases = []
        
        actions = req_data['actions']
        entities = req_data['entities']
        constraints = req_data['constraints']
        validations = req_data['validations']
        errors = req_data['error_scenarios']
        
        # 1. Positive Test
        test_cases.append(self._create_positive_test(req, actions, entities))
        
        # 2. Negative Test
        test_cases.append(self._create_negative_test(req, actions, entities, errors))
        
        # 3. Boundary Test
        if constraints:
            test_cases.append(self._create_boundary_test(req, actions, entities, constraints))
        
        # 4. Validation Test
        if validations:
            test_cases.append(self._create_validation_test(req, validations))
        
        # 5. Security Test
        test_cases.append(self._create_security_test(req, actions, entities))
        
        # 6. Error Handling Test
        if errors:
            test_cases.append(self._create_error_handling_test(req, errors))
        
        # 7. Edge Case Test
        test_cases.append(self._create_edge_case_test(req, actions, entities, constraints))
        
        # 8. Functional Test
        test_cases.append(self._create_functional_test(req, actions, entities))
        
        # 9. Data Consistency Test
        test_cases.append(self._create_data_consistency_test(req, actions, entities))
        
        # 10. Performance Test
        test_cases.append(self._create_performance_test(req, actions, entities))
        
        return test_cases
    
    def _create_positive_test(self, req, actions, entities):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        return {
            'steps': f'1. Prepare valid {entity} with all required data\n2. Execute {action} operation\n3. Verify system accepts input\n4. Confirm {action} completes successfully\n5. Verify success message and data saved',
            'expected': f'{action.capitalize()} operation succeeds with valid {entity}',
            'test_data': f'Valid {entity}: Complete and correct data',
            'type': 'Positive',
            'priority': 'High'
        }
    
    def _create_negative_test(self, req, actions, entities, errors):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        error = errors[0] if errors else 'Invalid input'
        return {
            'steps': f'1. Prepare invalid {entity}\n2. Attempt {action} operation\n3. Verify system rejects input\n4. Confirm error message displayed\n5. Verify {action} not executed',
            'expected': f'{action.capitalize()} operation fails with error: {error}',
            'test_data': f'Invalid {entity}: Missing or incorrect data',
            'type': 'Negative',
            'priority': 'High'
        }
    
    def _create_boundary_test(self, req, actions, entities, constraints):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        
        if 'max_limit' in constraints:
            return {
                'steps': f'1. Prepare {entity} at maximum allowed value\n2. Execute {action} operation\n3. Verify system accepts maximum\n4. Prepare {entity} exceeding maximum\n5. Verify system rejects excess',
                'expected': f'{action.capitalize()} accepts maximum but rejects excess',
                'test_data': f'{entity} at max boundary and beyond',
                'type': 'Boundary',
                'priority': 'High'
            }
        elif 'min_limit' in constraints:
            return {
                'steps': f'1. Prepare {entity} below minimum\n2. Attempt {action} operation\n3. Verify system rejects\n4. Prepare {entity} at minimum\n5. Verify system accepts',
                'expected': f'{action.capitalize()} rejects below minimum, accepts at minimum',
                'test_data': f'{entity} at min boundary',
                'type': 'Boundary',
                'priority': 'High'
            }
        else:
            return {
                'steps': f'1. Test {entity} with boundary values\n2. Execute {action} operation\n3. Verify system handles boundaries\n4. Check edge values\n5. Confirm proper handling',
                'expected': f'{action.capitalize()} handles boundary values correctly',
                'test_data': f'{entity} boundary test data',
                'type': 'Boundary',
                'priority': 'Medium'
            }
    
    def _create_validation_test(self, req, validations):
        validation = validations[0] if validations else 'Format validation'
        return {
            'steps': f'1. Enter invalid data violating {validation}\n2. Verify validation error\n3. Enter valid data meeting {validation}\n4. Verify system accepts\n5. Confirm validation enforced',
            'expected': f'{validation} is properly enforced',
            'test_data': f'Invalid: Non-compliant data, Valid: Compliant data',
            'type': 'Validation',
            'priority': 'High'
        }
    
    def _create_security_test(self, req, actions, entities):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        return {
            'steps': f'1. Attempt SQL injection in {entity} field\n2. Verify system sanitizes input\n3. Attempt XSS attack\n4. Verify no script execution\n5. Confirm secure handling',
            'expected': f'{action.capitalize()} securely handles malicious {entity}',
            'test_data': f'Malicious: SQL injection, XSS, command injection attempts',
            'type': 'Security',
            'priority': 'High'
        }
    
    def _create_error_handling_test(self, req, errors):
        error = errors[0] if errors else 'System error'
        return {
            'steps': f'1. Trigger {error} condition\n2. Verify error message displayed\n3. Check error is user-friendly\n4. Verify system state not corrupted\n5. Confirm recovery possible',
            'expected': f'{error} handled gracefully with clear message',
            'test_data': f'Error condition: {error}',
            'type': 'Error Handling',
            'priority': 'High'
        }
    
    def _create_edge_case_test(self, req, actions, entities, constraints):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        
        if 'uniqueness' in constraints:
            return {
                'steps': f'1. Create {entity} with unique value\n2. Attempt to create duplicate\n3. Verify system prevents duplicate\n4. Check error message\n5. Confirm uniqueness enforced',
                'expected': f'System prevents duplicate {entity}',
                'test_data': f'Duplicate {entity} with same unique value',
                'type': 'Edge Case',
                'priority': 'High'
            }
        else:
            return {
                'steps': f'1. Prepare {entity} with special characters\n2. Execute {action} operation\n3. Verify system handles special cases\n4. Check for unexpected behavior\n5. Confirm proper handling',
                'expected': f'{action.capitalize()} handles edge cases with {entity}',
                'test_data': f'{entity} with special characters/unicode',
                'type': 'Edge Case',
                'priority': 'Medium'
            }
    
    def _create_functional_test(self, req, actions, entities):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        return {
            'steps': f'1. Setup test environment\n2. Execute {action} operation\n3. Verify all system components respond\n4. Check data consistency\n5. Validate complete workflow',
            'expected': f'{action.capitalize()} operation functions correctly end-to-end',
            'test_data': f'Complete {entity} workflow data',
            'type': 'Functional',
            'priority': 'High'
        }
    
    def _create_data_consistency_test(self, req, actions, entities):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        return {
            'steps': f'1. Execute {action} operation\n2. Verify {entity} data saved correctly\n3. Retrieve {entity} from system\n4. Compare original and retrieved data\n5. Confirm data consistency',
            'expected': f'{entity} data remains consistent after {action}',
            'test_data': f'{entity} with various data types',
            'type': 'Data Consistency',
            'priority': 'High'
        }
    
    def _create_performance_test(self, req, actions, entities):
        action = actions[0] if actions else 'execute'
        entity = entities[0] if entities else 'item'
        return {
            'steps': f'1. Execute {action} operation\n2. Measure response time\n3. Verify response within acceptable time\n4. Test with multiple concurrent requests\n5. Confirm performance acceptable',
            'expected': f'{action.capitalize()} operation completes within acceptable time',
            'test_data': f'{entity} with performance monitoring',
            'type': 'Performance',
            'priority': 'Medium'
        }
    
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

    def _is_non_functional_requirement(self, req):
        """Detect if requirement is non-functional"""
        non_func_keywords = ['performance', 'scalability', 'usability', 'reliability', 'availability', 'maintainability', 'security', 'response time', 'throughput', 'latency', 'load', 'stress', 'concurrent', 'user-friendly', 'intuitive', 'accessible', 'compliant', 'standard', 'robust', 'resilient', 'fault-tolerant', 'backup', 'recovery', 'disaster', 'high availability', 'uptime', 'sla']
        return any(kw in req.lower() for kw in non_func_keywords)
    
    def _create_performance_requirement_test(self, req):
        """Create test for performance requirements"""
        return {
            'steps': '1. Setup performance monitoring tools\\n2. Execute operation under normal load\\n3. Measure response time\\n4. Verify meets performance criteria\\n5. Document results',
            'expected': 'Operation meets performance requirements',
            'test_data': 'Performance test data with monitoring',
            'type': 'Performance',
            'priority': 'High'
        }
    
    def _create_scalability_requirement_test(self, req):
        """Create test for scalability requirements"""
        return {
            'steps': '1. Setup test environment with baseline load\\n2. Gradually increase load\\n3. Monitor system performance\\n4. Verify system scales appropriately\\n5. Identify breaking points',
            'expected': 'System scales to handle increased load',
            'test_data': 'Scalability test with increasing load',
            'type': 'Scalability',
            'priority': 'High'
        }
    
    def _create_usability_requirement_test(self, req):
        """Create test for usability requirements"""
        return {
            'steps': '1. Conduct user testing\\n2. Verify UI is intuitive\\n3. Check navigation is clear\\n4. Verify error messages are helpful\\n5. Confirm accessibility standards met',
            'expected': 'System is user-friendly and accessible',
            'test_data': 'User testing with diverse user groups',
            'type': 'Usability',
            'priority': 'Medium'
        }
    
    def _create_reliability_requirement_test(self, req):
        """Create test for reliability requirements"""
        return {
            'steps': '1. Run system for extended period\\n2. Monitor for failures\\n3. Test error recovery\\n4. Verify data integrity\\n5. Confirm system stability',
            'expected': 'System operates reliably without failures',
            'test_data': 'Long-running reliability test',
            'type': 'Reliability',
            'priority': 'High'
        }
    
    def _create_availability_requirement_test(self, req):
        """Create test for availability requirements"""
        return {
            'steps': '1. Monitor system uptime\\n2. Simulate component failures\\n3. Verify failover mechanisms\\n4. Check recovery time\\n5. Confirm availability targets met',
            'expected': 'System meets availability requirements',
            'test_data': 'Availability test with failure scenarios',
            'type': 'Availability',
            'priority': 'High'
        }
