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
            r'login|logout|sign up|register',
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
        """Extract requirements from content with improved filtering and sentence grouping"""
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
            requirements = self._group_related_sentences(content)
        
        return requirements
    
    def _group_related_sentences(self, content):
        """Group related sentences together to keep context intact"""
        requirements = []
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', content)
        
        current_group = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or self._is_noise(sentence):
                continue
            
            current_group.append(sentence)
            
            if len(' '.join(current_group)) > 100 or sentence.endswith('.'):
                grouped = ' '.join(current_group).strip()
                if len(grouped) > 20:
                    requirements.append(grouped)
                current_group = []
        
        if current_group:
            grouped = ' '.join(current_group).strip()
            if len(grouped) > 20:
                requirements.append(grouped)
        
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
            
            test_cases = self._generate_comprehensive_tests(req)
            
            for test_case in test_cases:
                tc = {
                    'tc_id': f'TC_{tc_counter:02d}',
                    'steps': test_case['steps'],
                    'expected': test_case['expected'],
                    'test_data': test_case['test_data'],
                    'results': '',
                    'defects': '',
                    'comments': f"Type: {test_case['type']} | Category: {test_case['category']} | Priority: {test_case['priority']}"
                }
                scenario_obj['test_cases'].append(tc)
                tc_counter += 1
            
            results.append(scenario_obj)
            ts_counter += 1
        
        return results
    
    def _generate_comprehensive_tests(self, req):
        """Generate comprehensive test cases by analyzing requirement dynamically"""
        req_lower = req.lower()
        test_cases = []
        
        details = self._analyze_requirement(req, req_lower)
        
        test_cases.extend(self._generate_positive_tests(req, details))
        test_cases.extend(self._generate_negative_tests(req, details))
        test_cases.extend(self._generate_boundary_tests(req, details))
        test_cases.extend(self._generate_edge_case_tests(req, details))
        test_cases.extend(self._generate_error_handling_tests(req, details))
        test_cases.extend(self._generate_security_tests(req, details))
        test_cases.extend(self._generate_ui_interaction_tests(req, details))
        test_cases.extend(self._generate_workflow_tests(req, details))
        
        return test_cases
    
    def _analyze_requirement(self, req, req_lower):
        """Dynamically analyze requirement and extract all relevant details"""
        details = {
            'actor': self._extract_actor(req),
            'action': self._extract_action(req),
            'condition': self._extract_condition(req),
            'expected_outcome': self._extract_expected_outcome(req),
            'ui_elements': self._extract_ui_elements(req),
            'business_rules': self._extract_business_rules(req),
            'workflow_steps': self._extract_workflow_steps(req),
            'field_patterns': self._extract_field_patterns(req),
            'messages': self._extract_quoted_messages(req),
            'numbers': re.findall(r'\d+', req),
            'errors': self._extract_error_keywords(req_lower),
            'conditions': self._extract_condition_keywords(req_lower),
        }
        
        return details
    
    def _extract_actor(self, req):
        """Extract actor (who performs the action)"""
        actor_patterns = [
            r'(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:should|can|must|will|is able to)',
            r'(?:as\s+(?:a|an)\s+)?(\w+(?:\s+\w+)?)\s+(?:i\s+)?(?:want|need)',
        ]
        for pattern in actor_patterns:
            match = re.search(pattern, req, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "User"
    
    def _extract_action(self, req):
        """Extract primary action from requirement"""
        action_verbs = ['add', 'remove', 'delete', 'create', 'update', 'modify', 'edit', 'submit', 'upload', 'download', 'export', 'import', 'search', 'filter', 'sort', 'view', 'display', 'show', 'hide', 'enable', 'disable', 'lock', 'unlock', 'approve', 'reject', 'publish', 'unpublish', 'register', 'login', 'logout', 'verify', 'validate', 'authenticate', 'authorize', 'reset', 'recover', 'send', 'receive', 'retrieve', 'store', 'save', 'persist', 'cancel', 'confirm', 'accept', 'decline', 'process']
        
        for verb in action_verbs:
            if verb in req.lower():
                match = re.search(rf'{verb}\s+(\w+(?:\s+\w+)?)', req, re.IGNORECASE)
                if match:
                    return f"{verb} {match.group(1)}"
                return verb
        return "Perform operation"
    
    def _extract_condition(self, req):
        """Extract condition (when/if the action should happen)"""
        condition_patterns = [
            r'(?:if|when|unless|only if|provided that)\s+([^.!?]+)',
            r'using\s+([^.!?]+)',
            r'with\s+([^.!?]+)',
        ]
        for pattern in condition_patterns:
            match = re.search(pattern, req, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_expected_outcome(self, req):
        """Extract expected outcome/result"""
        outcome_patterns = [
            r'(?:should|must|will)\s+([^.!?]+)',
            r'(?:result|outcome|expect)\s+(?:is|should be)\s+([^.!?]+)',
            r'(?:then|so that)\s+([^.!?]+)',
        ]
        for pattern in outcome_patterns:
            match = re.search(pattern, req, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "Operation completes successfully"
    
    def _extract_ui_elements(self, req):
        """Extract UI elements mentioned in requirement"""
        ui_elements = []
        ui_keywords = {
            'button': r'\b(?:button|btn|click|submit|save|cancel|ok|close)\b',
            'field': r'\b(?:field|input|textbox|text box|text field|entry)\b',
            'dropdown': r'\b(?:dropdown|drop-down|select|combo box|list)\b',
            'checkbox': r'\b(?:checkbox|check box|tick|toggle)\b',
            'radio': r'\b(?:radio|radio button)\b',
            'link': r'\b(?:link|hyperlink|url)\b',
            'upload': r'\b(?:upload|file upload|attach|attachment)\b',
            'table': r'\b(?:table|grid|data grid)\b',
            'modal': r'\b(?:modal|dialog|popup|pop-up)\b',
            'menu': r'\b(?:menu|navigation|nav)\b',
        }
        
        for element_type, pattern in ui_keywords.items():
            if re.search(pattern, req, re.IGNORECASE):
                ui_elements.append(element_type)
        
        return ui_elements
    
    def _extract_business_rules(self, req):
        """Extract business rules and constraints"""
        rules = []
        
        constraint_patterns = [
            (r'(?:maximum|max|at most|not exceed|up to)\s+([\$]?\d+(?:\.\d{2})?)', 'max'),
            (r'(?:minimum|min|at least)\s+([\$]?\d+(?:\.\d{2})?)', 'min'),
            (r'(?:exactly|equal to)\s+([\$]?\d+(?:\.\d{2})?)', 'exact'),
            (r'([\$]?\d+(?:\.\d{2})?)\s+(?:items?|records?|characters?|bytes?|seconds?|minutes?|hours?|days?|documents?|files?)', 'count'),
        ]
        
        for pattern, rule_type in constraint_patterns:
            matches = re.findall(pattern, req, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    value = match[0]
                else:
                    value = match
                rules.append({'type': rule_type, 'value': value})
        
        return rules
    
    def _extract_workflow_steps(self, req):
        """Extract multi-step workflow from requirement"""
        steps = []
        
        workflow_indicators = ['then', 'after', 'next', 'subsequently', 'following', 'once', 'before', 'prior to']
        
        sentences = re.split(r'(?<=[.!?])\s+', req)
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in workflow_indicators):
                steps.append(sentence)
        
        if len(steps) > 1:
            return steps
        
        step_patterns = re.split(r'(?:then|after|next|subsequently|following|once|before|prior to)\s+', req, flags=re.IGNORECASE)
        if len(step_patterns) > 1:
            return [s.strip() for s in step_patterns if s.strip()]
        
        return []
    
    def _extract_field_patterns(self, req):
        """Dynamically extract field patterns from requirement text"""
        patterns = []
        
        field_pattern = r'(\w+(?:\s+\w+)*)\s+(?:field|input|value|parameter|attribute|property)'
        matches = re.findall(field_pattern, req, re.IGNORECASE)
        for match in matches:
            patterns.append(match.strip())
        
        return patterns
    
    def _extract_quoted_messages(self, req):
        """Extract quoted messages as complete units"""
        messages = re.findall(r'["\']([^"\']*)["\']', req)
        return messages
    
    def _extract_error_keywords(self, req_lower):
        """Extract error-related keywords"""
        error_keywords = ['error', 'fail', 'invalid', 'reject', 'deny', 'prevent', 'block', 'restrict', 'not allowed', 'forbidden', 'unauthorized', 'exception', 'warning', 'alert']
        errors = []
        for keyword in error_keywords:
            if keyword in req_lower:
                errors.append(keyword)
        return errors
    
    def _extract_condition_keywords(self, req_lower):
        """Extract condition keywords"""
        condition_keywords = ['if', 'when', 'unless', 'only if', 'provided that', 'in case', 'should', 'must', 'can', 'cannot', 'may', 'should not']
        conditions = []
        for keyword in condition_keywords:
            if keyword in req_lower:
                conditions.append(keyword)
        return conditions
    
    def _detect_field_type(self, field_name):
        """Detect field type based on field name patterns"""
        field_lower = field_name.lower()
        
        if any(keyword in field_lower for keyword in ['email', 'mail']):
            return 'email'
        elif any(keyword in field_lower for keyword in ['password', 'pwd', 'pass']):
            return 'password'
        elif any(keyword in field_lower for keyword in ['phone', 'mobile', 'contact']):
            return 'phone'
        elif any(keyword in field_lower for keyword in ['age', 'year', 'birth']):
            return 'age'
        elif any(keyword in field_lower for keyword in ['date', 'dob']):
            return 'date'
        elif any(keyword in field_lower for keyword in ['url', 'website', 'link']):
            return 'url'
        elif any(keyword in field_lower for keyword in ['amount', 'price', 'cost', 'salary']):
            return 'amount'
        elif any(keyword in field_lower for keyword in ['username', 'user', 'name']):
            return 'username'
        elif any(keyword in field_lower for keyword in ['zip', 'postal', 'code']):
            return 'zipcode'
        elif any(keyword in field_lower for keyword in ['credit', 'card', 'number']):
            return 'card'
        else:
            return 'text'
    
    def _generate_test_data(self, field_name, field_type=None):
        """Generate intelligent test data for detected field types"""
        if field_type is None:
            field_type = self._detect_field_type(field_name)
        
        test_data = {
            'valid': [],
            'invalid': [],
            'boundary': [],
            'edge_case': []
        }
        
        if field_type == 'email':
            test_data['valid'] = ['test@example.com', 'user.name@domain.co.uk', 'john123@company.org']
            test_data['invalid'] = ['test@', '@example.com', 'test@.com', 'test..@example.com', 'test@domain']
            test_data['boundary'] = ['a@b.co', 'verylongemailaddress@verylongdomainname.com']
            test_data['edge_case'] = ['test+tag@example.com', 'test_name@example.com', '123@example.com']
        
        elif field_type == 'password':
            test_data['valid'] = ['P@ssw0rd123', 'SecurePass!2024', 'MyP@ss123']
            test_data['invalid'] = ['123', 'password', 'pass', '12345678', 'abcdefgh']
            test_data['boundary'] = ['P@1', 'P@ssw0rd123456789012345']
            test_data['edge_case'] = ['P@ss!@#$%', 'Pass123!@#', 'P@ss 123']
        
        elif field_type == 'phone':
            test_data['valid'] = ['555-123-4567', '(555) 123-4567', '+1-555-123-4567', '5551234567']
            test_data['invalid'] = ['123', 'abc-def-ghij', '555-12-3456', '(555) 123']
            test_data['boundary'] = ['1234567', '55512345678901']
            test_data['edge_case'] = ['555-123-4567 ext 123', '+44-20-7946-0958', '001-555-123-4567']
        
        elif field_type == 'age':
            test_data['valid'] = ['25', '18', '65', '30']
            test_data['invalid'] = ['-5', '150', 'abc', '25.5']
            test_data['boundary'] = ['0', '1', '17', '18', '65', '120']
            test_data['edge_case'] = ['00', '018', '065']
        
        elif field_type == 'date':
            test_data['valid'] = ['12/25/2024', '01/01/2024', '06/15/2023']
            test_data['invalid'] = ['13/32/2024', '00/00/0000', '2024-12-25', '25-12-2024']
            test_data['boundary'] = ['01/01/1900', '12/31/2099', '02/29/2024']
            test_data['edge_case'] = ['02/29/2023', '12/31/1999', '01/01/2000']
        
        elif field_type == 'url':
            test_data['valid'] = ['https://example.com', 'http://www.example.com', 'https://example.com/path']
            test_data['invalid'] = ['example.com', 'htp://example.com', 'https://', 'https://example']
            test_data['boundary'] = ['https://a.co', 'https://verylongdomainname.com/very/long/path/structure']
            test_data['edge_case'] = ['https://example.com:8080', 'https://example.com/path?query=value', 'https://example.com#anchor']
        
        elif field_type == 'amount':
            test_data['valid'] = ['100.00', '50.50', '1000.99', '0.01']
            test_data['invalid'] = ['-50', 'abc', '100.999', '$100']
            test_data['boundary'] = ['0.00', '0.01', '999999.99', '1000000.00']
            test_data['edge_case'] = ['0.001', '100', '100.1', '100.10']
        
        elif field_type == 'username':
            test_data['valid'] = ['john_doe', 'user123', 'john.doe', 'johndoe']
            test_data['invalid'] = ['john doe', 'john@doe', 'j', 'john-doe-with-very-long-name']
            test_data['boundary'] = ['ab', 'a', 'verylongusernamethatexceedslimit']
            test_data['edge_case'] = ['user_123', 'user.123', 'user123_', '_user123']
        
        elif field_type == 'zipcode':
            test_data['valid'] = ['12345', '12345-6789', 'A1A 1A1']
            test_data['invalid'] = ['123', 'abcde', '12345-', '123-45']
            test_data['boundary'] = ['00000', '99999', '00000-0000']
            test_data['edge_case'] = ['12345-0000', 'A0A 0A0', '00001']
        
        elif field_type == 'card':
            test_data['valid'] = ['4532015112830366', '5425233010103442', '378282246310005']
            test_data['invalid'] = ['123456', 'abcd1234efgh5678', '4532015112830367']
            test_data['boundary'] = ['0000000000000000', '9999999999999999']
            test_data['edge_case'] = ['4532-0151-1283-0366', '4532 0151 1283 0366']
        
        else:  # text
            test_data['valid'] = ['Sample text', 'Valid input', 'Test data']
            test_data['invalid'] = ['', None]
            test_data['boundary'] = ['a', 'verylongtextthatmightexceedmaximumlength']
            test_data['edge_case'] = ['Text with @#$%', 'Text with 中文', 'Text with \n newline']
        
        return test_data
    
    def _generate_positive_tests(self, req, details):
        """Generate positive scenario tests"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        condition = details['condition']
        outcome = details['expected_outcome']
        field_patterns = details['field_patterns']
        
        if condition:
            steps = f'1. Ensure {condition}\n2. {actor} performs: {action}\n3. Verify system accepts input\n4. Confirm {action} completes\n5. Validate: {outcome}'
        else:
            steps = f'1. {actor} prepares for: {action}\n2. Execute {action}\n3. Verify system accepts input\n4. Confirm {action} completes\n5. Validate: {outcome}'
        
        test_data_str = f'Valid data for {action}'
        if field_patterns:
            field_data = []
            for field in field_patterns[:3]:
                test_data = self._generate_test_data(field)
                if test_data['valid']:
                    field_data.append(f"{field}: {test_data['valid'][0]}")
            if field_data:
                test_data_str = ' | '.join(field_data)
        
        tests.append({
            'type': 'Positive',
            'category': 'Positive Test',
            'priority': 'High',
            'steps': steps,
            'expected': outcome,
            'test_data': test_data_str
        })
        
        return tests
    
    def _generate_negative_tests(self, req, details):
        """Generate negative scenario tests"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        field_patterns = details['field_patterns']
        
        if details['errors']:
            error = details['errors'][0]
            test_data_str = 'Invalid data'
            if field_patterns:
                field_data = []
                for field in field_patterns[:3]:
                    test_data = self._generate_test_data(field)
                    if test_data['invalid']:
                        field_data.append(f"{field}: {test_data['invalid'][0]}")
                if field_data:
                    test_data_str = ' | '.join(field_data)
            
            tests.append({
                'type': 'Negative',
                'category': 'Negative Test',
                'priority': 'High',
                'steps': f'1. {actor} prepares invalid data\n2. Attempt to {action}\n3. Verify system rejects input\n4. Confirm {error} message displayed\n5. Validate operation not executed',
                'expected': f'System rejects with {error}',
                'test_data': test_data_str
            })
        else:
            test_data_str = 'Invalid data'
            if field_patterns:
                field_data = []
                for field in field_patterns[:3]:
                    test_data = self._generate_test_data(field)
                    if test_data['invalid']:
                        field_data.append(f"{field}: {test_data['invalid'][0]}")
                if field_data:
                    test_data_str = ' | '.join(field_data)
            
            tests.append({
                'type': 'Negative',
                'category': 'Negative Test',
                'priority': 'High',
                'steps': f'1. {actor} prepares invalid data\n2. Attempt to {action}\n3. Verify system rejects\n4. Confirm error message displayed\n5. Validate operation not executed',
                'expected': 'System rejects invalid input',
                'test_data': test_data_str
            })
        
        return tests
    
    def _generate_boundary_tests(self, req, details):
        """Generate boundary condition tests based on business rules"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        field_patterns = details['field_patterns']
        
        for rule in details['business_rules']:
            if rule['type'] in ['max', 'min']:
                try:
                    limit = float(rule['value'].replace('$', '').replace(',', ''))
                    if rule['type'] == 'max':
                        tests.append({
                            'type': 'Boundary',
                            'category': 'Boundary Value Test',
                            'priority': 'High',
                            'steps': f'1. {actor} attempts {action} with value at limit: {limit}\n2. Verify system accepts\n3. {actor} attempts with value exceeding: {limit + 1}\n4. Verify system rejects\n5. Confirm boundary enforced',
                            'expected': f'System enforces maximum limit of {limit}',
                            'test_data': f'At limit: {limit}, Exceeds: {limit + 1}, Below: {max(0, limit - 1)}'
                        })
                    else:
                        tests.append({
                            'type': 'Boundary',
                            'category': 'Boundary Value Test',
                            'priority': 'High',
                            'steps': f'1. {actor} attempts {action} with value below limit: {max(0, limit - 1)}\n2. Verify system rejects\n3. {actor} attempts with value at limit: {limit}\n4. Verify system accepts\n5. Confirm boundary enforced',
                            'expected': f'System enforces minimum limit of {limit}',
                            'test_data': f'Below limit: {max(0, limit - 1)}, At limit: {limit}, Above: {limit + 1}'
                        })
                except:
                    pass
        
        if field_patterns and not details['business_rules']:
            for field in field_patterns[:2]:
                test_data = self._generate_test_data(field)
                if test_data['boundary']:
                    boundary_values = ' | '.join(test_data['boundary'])
                    tests.append({
                        'type': 'Boundary',
                        'category': 'Boundary Value Test',
                        'priority': 'High',
                        'steps': f'1. {actor} enters boundary values for {field}\n2. Test minimum boundary\n3. Verify system response\n4. Test maximum boundary\n5. Confirm boundaries enforced',
                        'expected': f'System handles boundary values for {field} correctly',
                        'test_data': boundary_values
                    })
        
        return tests
    
    def _generate_edge_case_tests(self, req, details):
        """Generate edge case tests"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        field_patterns = details['field_patterns']
        
        if field_patterns:
            for field in field_patterns[:2]:
                test_data = self._generate_test_data(field)
                if test_data['edge_case']:
                    edge_values = ' | '.join(test_data['edge_case'])
                    tests.append({
                        'type': 'Edge Case',
                        'category': 'Edge Case Test',
                        'priority': 'Medium',
                        'steps': f'1. {actor} enters edge case values for {field}\n2. Execute {action}\n3. Verify system handles edge cases\n4. Check for unexpected behavior\n5. Confirm proper handling',
                        'expected': f'System handles edge cases for {field} correctly',
                        'test_data': edge_values
                    })
        
        tests.append({
            'type': 'Edge Case',
            'category': 'Edge Case Test',
            'priority': 'Medium',
            'steps': f'1. {actor} prepares data with special characters: @#$%^&*()\n2. Execute {action}\n3. Verify system handles special cases\n4. Check for unexpected behavior\n5. Confirm proper handling',
            'expected': 'System handles edge cases correctly',
            'test_data': 'Special characters: @#$%^&*(), Unicode: ñ, é, 中文'
        })
        
        tests.append({
            'type': 'Edge Case',
            'category': 'Edge Case Test',
            'priority': 'Medium',
            'steps': f'1. {actor} prepares empty/null data\n2. Execute {action}\n3. Verify system handles gracefully\n4. Check error handling\n5. Confirm no crashes occur',
            'expected': 'System handles empty/null data gracefully',
            'test_data': 'Empty strings, null values, whitespace'
        })
        
        return tests
    
    def _generate_error_handling_tests(self, req, details):
        """Generate error handling tests"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        
        if details['errors']:
            tests.append({
                'type': 'Error Handling',
                'category': 'Error Handling Test',
                'priority': 'High',
                'steps': f'1. {actor} triggers error condition\n2. Verify error is caught\n3. Confirm error message displayed\n4. Check error details\n5. Validate system recovers',
                'expected': 'System handles errors gracefully',
                'test_data': 'Error triggering scenarios'
            })
        
        if details['messages']:
            for msg in details['messages'][:1]:
                tests.append({
                    'type': 'Message Validation',
                    'category': 'Error Handling Test',
                    'priority': 'High',
                    'steps': f'1. {actor} triggers condition for message: "{msg}"\n2. Verify exact message displayed\n3. Check message visibility\n4. Verify message clarity\n5. Confirm message appropriate',
                    'expected': f'System displays message: "{msg}"',
                    'test_data': f'Condition to trigger: "{msg}"'
                })
        
        return tests
    
    def _generate_security_tests(self, req, details):
        """Generate security tests if applicable"""
        tests = []
        
        actor = details['actor']
        action = details['action']
        
        security_keywords = ['password', 'authenticate', 'authorize', 'permission', 'role', 'secure', 'encrypt', 'token', 'session', 'login', 'logout']
        
        if any(keyword in req.lower() for keyword in security_keywords):
            tests.append({
                'type': 'Security',
                'category': 'Security Test',
                'priority': 'High',
                'steps': f'1. {actor} attempts {action} without proper authentication\n2. Verify system denies access\n3. {actor} authenticates properly\n4. Attempt {action} again\n5. Verify system allows access',
                'expected': 'System enforces security controls',
                'test_data': 'Authenticated and unauthenticated scenarios'
            })
        
        return tests
    
    def _generate_ui_interaction_tests(self, req, details):
        """Generate UI interaction tests based on detected UI elements"""
        tests = []
        
        actor = details['actor']
        ui_elements = details['ui_elements']
        
        if ui_elements:
            for element in ui_elements[:2]:
                tests.append({
                    'type': 'UI Interaction',
                    'category': 'UI Interaction Test',
                    'priority': 'Medium',
                    'steps': f'1. {actor} locates {element}\n2. Verify {element} is visible and enabled\n3. Interact with {element}\n4. Verify response to interaction\n5. Confirm expected behavior',
                    'expected': f'{element} responds correctly to user interaction',
                    'test_data': f'Valid interaction with {element}'
                })
        
        return tests
    
    def _generate_workflow_tests(self, req, details):
        """Generate end-to-end workflow tests"""
        tests = []
        
        actor = details['actor']
        workflow_steps = details['workflow_steps']
        
        if len(workflow_steps) > 1:
            steps_text = '\n'.join([f'{i+1}. {step}' for i, step in enumerate(workflow_steps[:5])])
            tests.append({
                'type': 'Workflow',
                'category': 'End-to-End Test',
                'priority': 'High',
                'steps': f'{steps_text}\n6. Verify complete workflow execution',
                'expected': 'Complete workflow executes successfully in correct sequence',
                'test_data': 'Multi-step workflow data'
            })
        
        return tests
    
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
                        'comments': 'Type: Positive | Category: Positive Test | Priority: High'
                    }
                ]
            }
        ]
