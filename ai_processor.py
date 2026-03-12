import docx
import PyPDF2
import requests
from bs4 import BeautifulSoup
import re

class AIProcessor:
    def __init__(self):
        self.test_scenarios = []
        self.generated_scenarios = set()
        self.test_types = ['Positive', 'Negative', 'Boundary', 'Validation', 'Security', 'Functional', 'Message', 'Edge Case', 'Performance', 'Data Consistency']
    
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
            
            test_cases = self._generate_dynamic_test_cases(req_data)
            
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
        
        content = re.sub(r'System Name:.*?\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Functional Requirements\n', '', content, flags=re.IGNORECASE)
        content = re.sub(r'Non-Functional Requirements\n', '', content, flags=re.IGNORECASE)
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('·') or re.match(r'^\d+[\.\)]\s', line)):
                req = re.sub(r'^[•\-*·\d+\.\)]\s*', '', line).strip()
                if len(req) > 15:
                    requirements.append(req)
        
        if not requirements:
            sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and sentence and not any(x in sentence.lower() for x in ['system name', 'functional', 'requirements']):
                    requirements.append(sentence)
        
        if not requirements:
            for line in lines:
                line = line.strip()
                if len(line) > 20 and line and not any(x in line.lower() for x in ['system name', 'functional', 'requirements']):
                    requirements.append(line)
        
        return requirements
    
    def _analyze_requirements(self, requirements):
        """Analyze requirements and extract universal patterns"""
        analysis = {}
        
        for idx, req in enumerate(requirements):
            req_id = f'REQ-{idx+1}'
            analysis[req_id] = {
                'requirement': req,
                'actions': self._extract_universal_actions(req),
                'entities': self._extract_universal_entities(req),
                'conditions': self._extract_universal_conditions(req),
                'constraints': self._extract_universal_constraints(req),
                'messages': self._extract_messages(req),
                'numbers': self._extract_numbers(req),
                'error_keywords': self._extract_error_keywords(req)
            }
        
        return analysis
    
    def _extract_universal_actions(self, req):
        """Extract ANY action verb from requirement"""
        actions = set()
        action_patterns = ['browse', 'filter', 'sort', 'search', 'add', 'remove', 'update', 'delete', 'edit', 'view', 'display', 'show', 'hide', 'checkout', 'pay', 'purchase', 'cancel', 'borrow', 'return', 'mark', 'send', 'notify', 'prevent', 'allow', 'block', 'validate', 'verify', 'calculate', 'reduce', 'increase', 'create', 'register', 'login', 'logout', 'lock', 'unlock', 'generate', 'receive', 'download', 'upload', 'export', 'import', 'retry', 'reset', 'recover', 'restore', 'backup', 'sync', 'refresh', 'reload', 'submit', 'approve', 'reject', 'confirm', 'deny', 'enable', 'disable']
        
        req_lower = req.lower()
        for action in action_patterns:
            if action in req_lower:
                actions.add(action)
        
        return list(actions) if actions else ['execute']
    
    def _extract_universal_entities(self, req):
        """Extract ANY entity/object from requirement"""
        entities = set()
        entity_patterns = ['product', 'order', 'payment', 'cart', 'user', 'address', 'email', 'notification', 'book', 'account', 'form', 'item', 'inventory', 'stock', 'card', 'phone', 'password', 'event', 'registration', 'ticket', 'seat', 'confirmation', 'document', 'file', 'record', 'data', 'page', 'button', 'field', 'profile', 'dashboard', 'message', 'comment', 'review', 'rating', 'category', 'tag', 'filter', 'report', 'invoice', 'receipt', 'transaction', 'session', 'token', 'permission', 'role', 'copy', 'status', 'limit', 'count', 'date', 'time', 'link', 'request', 'response']
        
        req_lower = req.lower()
        for entity in entity_patterns:
            if entity in req_lower:
                entities.add(entity)
        
        return list(entities) if entities else ['item']
    
    def _extract_universal_conditions(self, req):
        """Extract ANY condition from requirement"""
        conditions = set()
        
        if any(x in req.lower() for x in ['if', 'when', 'while']):
            conditions.add('conditional')
        if any(x in req.lower() for x in ['must', 'should', 'required', 'mandatory']):
            conditions.add('mandatory')
        if any(x in req.lower() for x in ['can', 'able to', 'may', 'allow']):
            conditions.add('capability')
        if any(x in req.lower() for x in ['not', 'cannot', 'should not', 'prevent', 'block']):
            conditions.add('restriction')
        if any(x in req.lower() for x in ['before', 'after', 'during', 'within']):
            conditions.add('temporal')
        if any(x in req.lower() for x in ['only', 'only if', 'unless']):
            conditions.add('exclusive')
        if any(x in req.lower() for x in ['and', 'or', 'both']):
            conditions.add('logical')
        
        return list(conditions) if conditions else ['standard']
    
    def _extract_universal_constraints(self, req):
        """Extract ANY constraint from requirement"""
        constraints = set()
        
        if any(x in req.lower() for x in ['maximum', 'max', 'limit', 'exceed', 'more than', 'not more', 'up to']):
            constraints.add('max_limit')
        if any(x in req.lower() for x in ['minimum', 'min', 'at least', 'exactly', 'no less']):
            constraints.add('min_limit')
        if any(x in req.lower() for x in ['length', 'character', 'digit', 'number', 'format', 'valid', 'pattern']):
            constraints.add('format')
        if any(x in req.lower() for x in ['available', 'exist', 'present', 'full', 'empty', 'out of stock', 'unavailable']):
            constraints.add('availability')
        if any(x in req.lower() for x in ['unique', 'duplicate', 'distinct', 'same', 'twice', 'simultaneously']):
            constraints.add('uniqueness')
        if any(x in req.lower() for x in ['time', 'minute', 'hour', 'day', 'week', 'month', 'year', 'second', 'duration', 'timeout', 'expir']):
            constraints.add('time_based')
        if any(x in req.lower() for x in ['email', 'phone', 'address', 'name', 'payment', 'credit', 'debit']):
            constraints.add('field_validation')
        
        return list(constraints) if constraints else []
    
    def _extract_messages(self, req):
        """Extract specific messages from requirement"""
        messages = re.findall(r'"([^"]*)"', req)
        return messages if messages else []
    
    def _extract_numbers(self, req):
        """Extract numbers (limits, days, etc.)"""
        numbers = re.findall(r'\d+', req)
        return numbers if numbers else []
    
    def _extract_error_keywords(self, req):
        """Extract error-related keywords"""
        errors = set()
        error_patterns = ['invalid', 'incorrect', 'wrong', 'error', 'fail', 'failed', 'failure', 'prevent', 'block', 'deny', 'reject', 'lock', 'locked', 'unavailable', 'not found', 'missing', 'required', 'empty', 'duplicate', 'exceed', 'limit']
        
        req_lower = req.lower()
        for error in error_patterns:
            if error in req_lower:
                errors.add(error)
        
        return list(errors) if errors else []
    
    def _generate_dynamic_test_cases(self, req_data):
        """Generate dynamic test cases with 75%+ coverage for ANY requirement"""
        req = req_data['requirement']
        actions = req_data['actions']
        entities = req_data['entities']
        conditions = req_data['conditions']
        constraints = req_data['constraints']
        messages = req_data['messages']
        numbers = req_data['numbers']
        errors = req_data['error_keywords']
        
        test_cases = []
        req_lower = req.lower()
        
        action = self._select_primary_action(actions, req_lower)
        entity = self._select_primary_entity(entities, req_lower)
        
        # Generate all 10 test types dynamically
        test_cases.append(self._generate_positive_test(action, entity, req_lower))
        test_cases.append(self._generate_negative_test(action, entity, req_lower))
        test_cases.append(self._generate_boundary_test(action, entity, constraints, numbers, req_lower))
        test_cases.append(self._generate_validation_test(action, entity, constraints, req_lower))
        test_cases.append(self._generate_security_test(action, entity, req_lower))
        test_cases.append(self._generate_functional_test(action, entity, conditions, req_lower))
        test_cases.append(self._generate_message_test(action, entity, messages, req_lower))
        test_cases.append(self._generate_edge_case_test(action, entity, constraints, req_lower))
        test_cases.append(self._generate_performance_test(action, entity, req_lower))
        test_cases.append(self._generate_data_consistency_test(action, entity, req_lower))
        
        return test_cases
    
    def _generate_positive_test(self, action, entity, req_lower):
        """Generate positive test case"""
        return {
            'steps': f'1. Prepare valid {entity} with all required data\n2. Execute {action} operation\n3. Verify system accepts input\n4. Confirm {action} completes successfully\n5. Verify success message and data saved',
            'expected': f'{action.capitalize()} operation succeeds with valid {entity}',
            'test_data': f'Valid {entity}: Complete and correct data',
            'type': 'Positive',
            'priority': 'High'
        }
    
    def _generate_negative_test(self, action, entity, req_lower):
        """Generate negative test case"""
        return {
            'steps': f'1. Prepare invalid {entity}\n2. Attempt {action} operation\n3. Verify system rejects input\n4. Confirm error message displayed\n5. Verify {action} not executed',
            'expected': f'{action.capitalize()} operation fails with appropriate error message',
            'test_data': f'Invalid {entity}: Missing or incorrect data',
            'type': 'Negative',
            'priority': 'High'
        }
    
    def _generate_boundary_test(self, action, entity, constraints, numbers, req_lower):
        """Generate boundary test case"""
        if 'max_limit' in constraints and numbers:
            limit = numbers[0]
            return {
                'steps': f'1. {action.capitalize()} {entity} at maximum limit ({limit})\n2. Verify system accepts\n3. Attempt to {action} {entity} exceeding limit ({int(limit)+1})\n4. Verify system rejects with appropriate message\n5. Confirm limit enforced',
                'expected': f'System accepts {entity} up to {limit}, rejects beyond limit',
                'test_data': f'{entity} count: {limit} (accepted), {int(limit)+1} (rejected)',
                'type': 'Boundary',
                'priority': 'High'
            }
        elif 'time_based' in constraints and numbers:
            days = numbers[0]
            return {
                'steps': f'1. {action.capitalize()} {entity}\n2. Wait {days} days\n3. Verify status remains normal\n4. Wait 1 more day (day {int(days)+1})\n5. Verify status changes appropriately',
                'expected': f'System enforces {days}-day rule correctly',
                'test_data': f'Time-based test: {days} days and {int(days)+1} days',
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
    
    def _generate_validation_test(self, action, entity, constraints, req_lower):
        """Generate validation test case"""
        if 'format' in constraints or 'field_validation' in constraints:
            return {
                'steps': f'1. Enter invalid format for {entity}\n2. Verify validation error\n3. Enter valid format\n4. Verify system accepts\n5. Confirm validation enforced',
                'expected': f'Format validation properly enforced for {entity}',
                'test_data': f'Invalid and valid formats for {entity}',
                'type': 'Validation',
                'priority': 'High'
            }
        else:
            return {
                'steps': f'1. Enter invalid data for {entity}\n2. Verify validation error\n3. Enter valid data\n4. Verify system accepts\n5. Confirm validation enforced',
                'expected': f'Validation properly enforced for {entity}',
                'test_data': f'Invalid and valid data for {entity}',
                'type': 'Validation',
                'priority': 'High'
            }
    
    def _generate_security_test(self, action, entity, req_lower):
        """Generate security test case"""
        return {
            'steps': f'1. Attempt SQL injection in {entity} field\n2. Verify system sanitizes input\n3. Attempt XSS attack\n4. Verify no script execution\n5. Confirm secure handling',
            'expected': f'{action.capitalize()} securely handles malicious {entity}',
            'test_data': f'Malicious: SQL injection, XSS, command injection attempts',
            'type': 'Security',
            'priority': 'High'
        }
    
    def _generate_functional_test(self, action, entity, conditions, req_lower):
        """Generate functional test case"""
        if 'restriction' in conditions or 'mandatory' in conditions:
            if 'login' in req_lower or 'logged in' in req_lower:
                return {
                    'steps': f'1. Attempt {action} without login\n2. Verify system redirects to login\n3. Login with valid credentials\n4. Attempt {action} again\n5. Verify action succeeds after login',
                    'expected': f'{action.capitalize()} respects all conditional requirements',
                    'test_data': f'Condition met and not met scenarios for {entity}',
                    'type': 'Functional',
                    'priority': 'High'
                }
            elif 'available' in req_lower or 'stock' in req_lower:
                return {
                    'steps': f'1. Verify {entity} availability/stock status\n2. Attempt {action} when available\n3. Verify action succeeds\n4. Attempt {action} when unavailable/out of stock\n5. Verify action prevented with error message',
                    'expected': f'{action.capitalize()} respects all conditional requirements',
                    'test_data': f'Condition met and not met scenarios for {entity}',
                    'type': 'Functional',
                    'priority': 'High'
                }
            else:
                return {
                    'steps': f'1. Verify condition for {action}\n2. Test when condition is met\n3. Verify {action} allowed\n4. Test when condition not met\n5. Verify {action} prevented',
                    'expected': f'{action.capitalize()} respects all conditional requirements',
                    'test_data': f'Condition met and not met scenarios for {entity}',
                    'type': 'Functional',
                    'priority': 'High'
                }
        else:
            return {
                'steps': f'1. Verify functionality for {action}\n2. Test with valid {entity}\n3. Verify {action} works correctly\n4. Check all features enabled\n5. Confirm functionality complete',
                'expected': f'{action.capitalize()} functionality works as expected',
                'test_data': f'Valid {entity} for functional testing',
                'type': 'Functional',
                'priority': 'High'
            }
    
    def _generate_message_test(self, action, entity, messages, req_lower):
        """Generate message test case"""
        if messages:
            msg = messages[0]
            return {
                'steps': f'1. Trigger condition for message: "{msg}"\n2. Verify exact message displayed\n3. Check message visibility\n4. Verify message formatting\n5. Confirm message clarity',
                'expected': f'System displays exact message: "{msg}"',
                'test_data': f'Message trigger: "{msg}"',
                'type': 'Functional',
                'priority': 'High'
            }
        else:
            return {
                'steps': f'1. Execute {action} operation\n2. Verify success/error message displayed\n3. Check message visibility\n4. Verify message formatting\n5. Confirm message clarity',
                'expected': f'System displays appropriate message for {action}',
                'test_data': f'Message display test data',
                'type': 'Functional',
                'priority': 'High'
            }
    
    def _generate_edge_case_test(self, action, entity, constraints, req_lower):
        """Generate edge case test case"""
        if 'uniqueness' in constraints:
            return {
                'steps': f'1. {action.capitalize()} {entity} with unique identifier\n2. Attempt to {action} same {entity} again\n3. Verify system prevents duplicate\n4. Check error message\n5. Confirm uniqueness enforced',
                'expected': f'System prevents duplicate {action} on same {entity}',
                'test_data': f'Duplicate {action} attempt on {entity}',
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
    
    def _generate_performance_test(self, action, entity, req_lower):
        """Generate performance test case"""
        return {
            'steps': f'1. Execute {action} operation\n2. Measure response time\n3. Verify response within acceptable time\n4. Test with multiple concurrent requests\n5. Confirm performance acceptable',
            'expected': f'{action.capitalize()} operation completes within acceptable time',
            'test_data': f'{entity} with performance monitoring',
            'type': 'Performance',
            'priority': 'Medium'
        }
    
    def _generate_data_consistency_test(self, action, entity, req_lower):
        """Generate data consistency test case"""
        return {
            'steps': f'1. Execute {action} operation\n2. Verify {entity} data saved correctly\n3. Retrieve {entity} from system\n4. Compare original and retrieved data\n5. Confirm data consistency',
            'expected': f'{entity} data remains consistent after {action}',
            'test_data': f'{entity} with various data types',
            'type': 'Data Consistency',
            'priority': 'High'
        }
    
    def _select_primary_action(self, actions, req_lower):
        """Select most relevant action based on requirement context"""
        priority_actions = ['browse', 'filter', 'sort', 'search', 'add', 'remove', 'update', 'checkout', 'pay', 'purchase', 'cancel', 'borrow', 'return', 'view', 'display', 'mark', 'send', 'prevent', 'validate', 'verify', 'calculate', 'reduce', 'increase']
        for action in priority_actions:
            if action in actions:
                return action
        return actions[0] if actions else 'execute'
    
    def _select_primary_entity(self, entities, req_lower):
        """Select most relevant entity based on requirement context"""
        if 'calculate' in req_lower or 'total price' in req_lower or 'tax' in req_lower:
            return 'order'
        if 'maximum quantity' in req_lower or 'add 11th' in req_lower or 'exceed' in req_lower:
            return 'product'
        if 'shipping address' in req_lower or 'enter address' in req_lower:
            return 'address'
        if 'credit card' in req_lower or 'card number' in req_lower or '16 digit' in req_lower:
            return 'card'
        if 'email' in req_lower or 'email format' in req_lower:
            return 'email'
        if 'phone' in req_lower or 'phone number' in req_lower or '10 digit' in req_lower:
            return 'phone'
        if 'inventory' in req_lower or 'stock' in req_lower or 'reduce' in req_lower or 'increase' in req_lower:
            return 'inventory'
        
        priority_entities = ['product', 'order', 'payment', 'cart', 'user', 'address', 'email', 'notification', 'book', 'account', 'form', 'inventory', 'stock', 'card', 'phone']
        for entity in priority_entities:
            if entity in entities:
                return entity
        return entities[0] if entities else 'item'
    
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
