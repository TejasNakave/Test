"""
Data-Driven Trade Filter Service
Analyzes actual document content to create dynamic topic filtering
Restricts chatbot to only answer questions related to available trade data
"""
import os
import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from collections import Counter, defaultdict
import json
import yaml
from datetime import datetime

# ChromaDB imports for analyzing indexed content
try:
    import chromadb
    from chromadb.api import ClientAPI
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class DataAnalysis:
    """Results of analyzing the actual trade data"""
    total_documents: int
    key_topics: List[str]
    trade_entities: Set[str]
    document_categories: Dict[str, List[str]]
    coverage_areas: List[str]
    confidence_keywords: Dict[str, float]

@dataclass
class TopicClassification:
    is_data_related: bool
    confidence_score: float
    matched_topics: List[str]
    relevant_documents: List[str]
    reason: str
    coverage_gap: bool

class DataDrivenTradeFilter:
    def __init__(self, 
                 data_folder: str = "data", 
                 chroma_db_path: str = "chroma_db",
                 config_output_path: str = "config/data_driven_config.yaml"):
        
        self.data_folder = data_folder
        self.chroma_db_path = chroma_db_path
        self.config_output_path = config_output_path
        
        # Analysis results
        self.data_analysis: Optional[DataAnalysis] = None
        self.document_topics: Dict[str, List[str]] = {}
        self.topic_document_map: Dict[str, List[str]] = defaultdict(list)
        self.coverage_keywords: Set[str] = set()
        
        # Initialize analysis
        self._analyze_data_content()
    
    def _analyze_data_content(self):
        """Analyze the actual trade documents to understand coverage"""
        logger.info("🔍 Analyzing actual trade document content...")
        
        try:
            # 1. Analyze document filenames for topics
            document_topics = self._analyze_document_filenames()
            
            # 2. Analyze ChromaDB content if available
            if CHROMA_AVAILABLE:
                indexed_content = self._analyze_chromadb_content()
            else:
                indexed_content = {}
            
            # 3. Extract key topics and entities
            key_topics, trade_entities = self._extract_topics_and_entities(document_topics, indexed_content)
            
            # 4. Categorize documents
            document_categories = self._categorize_documents(document_topics)
            
            # 5. Determine coverage areas
            coverage_areas = self._determine_coverage_areas(document_categories)
            
            # 6. Calculate confidence keywords
            confidence_keywords = self._calculate_confidence_keywords(key_topics, trade_entities)
            
            # Store analysis results
            self.data_analysis = DataAnalysis(
                total_documents=len(document_topics),
                key_topics=key_topics,
                trade_entities=trade_entities,
                document_categories=document_categories,
                coverage_areas=coverage_areas,
                confidence_keywords=confidence_keywords
            )
            
            # Generate dynamic configuration
            self._generate_dynamic_config()
            
            logger.info(f"✅ Data analysis complete: {len(key_topics)} topics, {len(trade_entities)} entities, {len(coverage_areas)} coverage areas")
            
        except Exception as e:
            logger.error(f"Error analyzing data content: {e}")
            self._create_fallback_analysis()
    
    def _analyze_document_filenames(self) -> Dict[str, List[str]]:
        """Extract topics from document filenames"""
        document_topics = {}
        
        if not os.path.exists(self.data_folder):
            logger.warning(f"Data folder {self.data_folder} not found")
            return document_topics
        
        for filename in os.listdir(self.data_folder):
            if filename.lower().endswith(('.docx', '.pdf', '.txt')):
                # Extract meaningful topics from filename
                topics = self._extract_topics_from_filename(filename)
                document_topics[filename] = topics
                
                # Update topic-document mapping
                for topic in topics:
                    self.topic_document_map[topic].append(filename)
        
        logger.info(f"📁 Analyzed {len(document_topics)} documents from filenames")
        return document_topics
    
    def _extract_topics_from_filename(self, filename: str) -> List[str]:
        """Extract trade topics from document filename"""
        filename_clean = filename.replace('.docx', '').replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Common trade topic patterns in your data
        trade_patterns = {
            'dgft': ['dgft', 'directorate general foreign trade', 'foreign trade policy'],
            'export': ['export', 'exporting', 'exporter', 'export house', 'export oriented'],
            'import': ['import', 'importing', 'importer', 'import clearance'],
            'customs': ['custom', 'customs', 'duty', 'tariff', 'clearance'],
            'certification': ['certificate', 'certification', 'aeo', 'chartered engineer'],
            'valuation': ['valuation', 'valuations', 'svb'],
            'classification': ['hsn', 'classification', 'sion'],
            'schemes': ['epcg', 'seis', 'drawback', 'rodtep', 'rosctl', 'meis'],
            'authorization': ['advance authorization', 'authorization', 'licence', 'license'],
            'compliance': ['compliance', 'policy', 'regulatory', 'fta', 'wto'],
            'documentation': ['documents', 'documentation', 'procedures', 'formalities'],
            'dispute': ['dispute', 'grievance', 'appeal', 'adjudication', 'seizure'],
            'warehousing': ['warehouse', 'warehousing', 'bonded', 'factory stuffing'],
            'logistics': ['transport', 'consolidation', 'icd', 'cfs', 'cargo'],
            'trade_operations': ['merchant export', 'deemed export', 'high sea sales', 're-export'],
            'special_procedures': ['baggage', 'second hand goods', 'samples']
        }
        
        extracted_topics = []
        filename_lower = filename_clean.lower()
        
        for category, keywords in trade_patterns.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    extracted_topics.append(category)
                    break
        
        # Extract specific document topics
        if 'getting started' in filename_lower:
            extracted_topics.append('beginner_guide')
        if 'flowchart' in filename_lower:
            extracted_topics.append('process_flow')
        if 'checklist' in filename_lower:
            extracted_topics.append('compliance_checklist')
        
        return list(set(extracted_topics))
    
    def _analyze_chromadb_content(self) -> Dict[str, Any]:
        """Analyze indexed content in ChromaDB"""
        indexed_content = {
            'documents': [],
            'topics': set(),
            'entities': set()
        }
        
        try:
            if not os.path.exists(self.chroma_db_path):
                logger.warning(f"ChromaDB path {self.chroma_db_path} not found")
                return indexed_content
            
            # Connect to ChromaDB
            client = chromadb.PersistentClient(path=self.chroma_db_path)
            collections = client.list_collections()
            
            for collection in collections:
                try:
                    # Get sample documents to analyze content
                    results = collection.peek(limit=50)
                    
                    for doc in results.get('documents', []):
                        if doc:
                            indexed_content['documents'].append(doc[:500])  # Sample content
                            
                            # Extract topics from content
                            content_topics = self._extract_topics_from_content(doc)
                            indexed_content['topics'].update(content_topics)
                            
                            # Extract entities
                            content_entities = self._extract_entities_from_content(doc)
                            indexed_content['entities'].update(content_entities)
                
                except Exception as e:
                    logger.warning(f"Error analyzing collection {collection.name}: {e}")
                    continue
            
            logger.info(f"📊 Analyzed ChromaDB: {len(indexed_content['documents'])} documents, {len(indexed_content['topics'])} topics")
            
        except Exception as e:
            logger.warning(f"Error connecting to ChromaDB: {e}")
        
        return indexed_content
    
    def _extract_topics_from_content(self, content: str) -> Set[str]:
        """Extract trade topics from document content"""
        topics = set()
        content_lower = content.lower()
        
        # Trade-specific patterns found in your documents
        topic_patterns = {
            'iec_procedures': ['iec', 'import export code', 'iec application'],
            'export_procedures': ['export procedure', 'export process', 'export clearance'],
            'import_procedures': ['import procedure', 'import process', 'import clearance'],
            'customs_procedures': ['customs clearance', 'customs procedure', 'customs process'],
            'duty_calculations': ['duty calculation', 'custom duty', 'tariff calculation'],
            'hsn_classification': ['hsn code', 'harmonized system', 'classification'],
            'export_incentives': ['export incentive', 'duty drawback', 'export promotion'],
            'dgft_schemes': ['dgft scheme', 'advance authorization', 'epcg'],
            'trade_agreements': ['free trade agreement', 'fta', 'preferential trade'],
            'compliance_requirements': ['compliance', 'regulatory requirement', 'trade policy'],
            'documentation': ['trade documentation', 'export documentation', 'import documentation'],
            'licensing': ['export license', 'import license', 'trade license'],
            'valuation_procedures': ['customs valuation', 'transaction value', 'valuation method'],
            'dispute_resolution': ['trade dispute', 'customs dispute', 'appeal procedure']
        }
        
        for topic_key, patterns in topic_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    topics.add(topic_key)
                    break
        
        return topics
    
    def _extract_entities_from_content(self, content: str) -> Set[str]:
        """Extract trade entities from document content"""
        entities = set()
        
        # Entity patterns specific to Indian trade
        entity_patterns = [
            r'\b(DGFT|CBIC|CBEC|RBI|SEBI|FIDR)\b',
            r'\b(IEC|Export Import Code)\b',
            r'\b(EPCG|Export Promotion Capital Goods)\b',
            r'\b(SEIS|MEIS|RoDTEP|ROSCTL)\b',
            r'\b(AEO|Authorized Economic Operator)\b',
            r'\b(HSN|Harmonized System)\b',
            r'\b(FTA|Free Trade Agreement)\b',
            r'\b(SEZ|Special Economic Zone|EOU)\b',
            r'\b(CFS|Container Freight Station|ICD)\b',
            r'\b(FOB|CIF|CFR|Ex[- ]?Works)\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.update([match.upper() if isinstance(match, str) else match[0].upper() for match in matches])
        
        return entities
    
    def _categorize_documents(self, document_topics: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Categorize documents by trade areas"""
        categories = defaultdict(list)
        
        for doc_name, topics in document_topics.items():
            # Primary categorization based on main topics
            if any(topic in ['dgft', 'schemes', 'authorization'] for topic in topics):
                categories['DGFT_Schemes'].append(doc_name)
            elif any(topic in ['export', 'export_procedures'] for topic in topics):
                categories['Export_Operations'].append(doc_name)
            elif any(topic in ['import', 'import_procedures'] for topic in topics):
                categories['Import_Operations'].append(doc_name)
            elif any(topic in ['customs', 'classification', 'valuation'] for topic in topics):
                categories['Customs_Procedures'].append(doc_name)
            elif any(topic in ['certification', 'compliance'] for topic in topics):
                categories['Compliance_Certification'].append(doc_name)
            elif any(topic in ['dispute', 'grievance'] for topic in topics):
                categories['Dispute_Resolution'].append(doc_name)
            elif any(topic in ['warehousing', 'logistics'] for topic in topics):
                categories['Logistics_Operations'].append(doc_name)
            else:
                categories['General_Trade'].append(doc_name)
        
        return dict(categories)
    
    def _determine_coverage_areas(self, document_categories: Dict[str, List[str]]) -> List[str]:
        """Determine what trade areas are covered by the data"""
        coverage_areas = []
        
        for category, docs in document_categories.items():
            if docs:  # If category has documents
                area_description = {
                    'DGFT_Schemes': 'DGFT policies, export promotion schemes, and government incentives',
                    'Export_Operations': 'Export procedures, documentation, and clearance processes',
                    'Import_Operations': 'Import procedures, licensing, and clearance processes', 
                    'Customs_Procedures': 'Customs duty, valuation, classification, and clearance',
                    'Compliance_Certification': 'Trade compliance, certifications, and regulatory requirements',
                    'Dispute_Resolution': 'Trade disputes, appeals, and grievance resolution',
                    'Logistics_Operations': 'Warehousing, logistics, and supply chain operations',
                    'General_Trade': 'General trade operations and miscellaneous procedures'
                }.get(category, f'{category} operations')
                
                coverage_areas.append(area_description)
        
        return coverage_areas
    
    def _calculate_confidence_keywords(self, key_topics: List[str], trade_entities: Set[str]) -> Dict[str, float]:
        """Calculate confidence scores for keywords based on data coverage"""
        confidence_keywords = {}
        
        # High confidence - core topics well covered in data
        for topic in key_topics:
            doc_count = len(self.topic_document_map.get(topic, []))
            confidence = min(doc_count / 10.0, 1.0)  # Max confidence at 10+ docs
            confidence_keywords[topic] = confidence
        
        # Medium confidence - entities mentioned
        for entity in trade_entities:
            confidence_keywords[entity.lower()] = 0.8
        
        # Topic-specific keywords with confidence based on coverage
        topic_keywords = {
            'export': 0.9 if any('export' in topic for topic in key_topics) else 0.3,
            'import': 0.9 if any('import' in topic for topic in key_topics) else 0.3,
            'customs': 0.8 if any('customs' in topic for topic in key_topics) else 0.3,
            'dgft': 0.9 if any('dgft' in topic for topic in key_topics) else 0.2,
            'documentation': 0.7,
            'compliance': 0.7,
            'trade': 0.8
        }
        
        confidence_keywords.update(topic_keywords)
        return confidence_keywords
    
    def _extract_topics_and_entities(self, document_topics: Dict[str, List[str]], indexed_content: Dict[str, Any]) -> Tuple[List[str], Set[str]]:
        """Extract all key topics and entities from the analysis"""
        all_topics = set()
        all_entities = set()
        
        # From document filenames
        for topics in document_topics.values():
            all_topics.update(topics)
        
        # From indexed content
        all_topics.update(indexed_content.get('topics', set()))
        all_entities.update(indexed_content.get('entities', set()))
        
        return sorted(list(all_topics)), all_entities
    
    def _create_fallback_analysis(self):
        """Create fallback analysis if data analysis fails"""
        logger.warning("🔄 Creating fallback trade analysis...")
        
        self.data_analysis = DataAnalysis(
            total_documents=0,
            key_topics=['export', 'import', 'customs', 'dgft', 'trade'],
            trade_entities={'DGFT', 'CBIC', 'IEC', 'HSN'},
            document_categories={'General_Trade': []},
            coverage_areas=['Basic trade operations'],
            confidence_keywords={'trade': 0.5, 'export': 0.5, 'import': 0.5}
        )
    
    def _generate_dynamic_config(self):
        """Generate dynamic configuration based on data analysis"""
        if not self.data_analysis:
            return
        
        config = {
            'data_driven_trade_filter': {
                'enabled': True,
                'last_updated': datetime.now().isoformat(),
                'data_analysis_summary': {
                    'total_documents': self.data_analysis.total_documents,
                    'coverage_areas': self.data_analysis.coverage_areas,
                    'key_topics_count': len(self.data_analysis.key_topics),
                    'entities_count': len(self.data_analysis.trade_entities)
                },
                
                # Dynamic allowed topics based on actual data
                'allowed_topics': {
                    topic: {
                        'confidence': self.data_analysis.confidence_keywords.get(topic, 0.5),
                        'related_documents': len(self.topic_document_map.get(topic, [])),
                        'enabled': True
                    }
                    for topic in self.data_analysis.key_topics
                },
                
                # Entity patterns from actual data
                'data_entities': list(self.data_analysis.trade_entities),
                
                # Document categories coverage
                'coverage_categories': self.data_analysis.document_categories,
                
                # Confidence thresholds
                'confidence_thresholds': {
                    'high_confidence': 0.8,  # Topics well covered in data
                    'medium_confidence': 0.5,  # Topics mentioned in data
                    'low_confidence': 0.2  # Topics barely covered
                },
                
                # Redirect responses based on actual coverage
                'data_coverage_response': {
                    'template': self._generate_coverage_response_template(),
                    'available_areas': self.data_analysis.coverage_areas,
                    'total_documents': self.data_analysis.total_documents
                }
            }
        }
        
        # Save configuration
        self._save_config(config)
    
    def _generate_coverage_response_template(self) -> str:
        """Generate response template based on actual data coverage"""
        return f"""🚀 **Trade Data Assistant - Powered by {self.data_analysis.total_documents} Trade Documents**

I can help you with questions related to the comprehensive trade data I have access to:

📋 **My Data Coverage Areas:**
{chr(10).join([f"- {area}" for area in self.data_analysis.coverage_areas])}

💡 **Example topics I can answer:**
{chr(10).join([f"- {topic.replace('_', ' ').title()}" for topic in self.data_analysis.key_topics[:8]])}

🎯 **Your question**: "{{question}}" doesn't match my trade data coverage.

**Please ask about:**
- Export-import procedures and documentation
- DGFT schemes and policies
- Customs procedures and compliance
- Trade certifications and licensing
- Any topic covered in my {self.data_analysis.total_documents} trade documents

I'm designed to provide accurate answers based on verified trade documentation! 🌟"""
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_output_path), exist_ok=True)
            with open(self.config_output_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            logger.info(f"✅ Data-driven config saved to {self.config_output_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def classify_question(self, question: str) -> TopicClassification:
        """Classify question based on actual data coverage"""
        if not self.data_analysis:
            return TopicClassification(
                is_data_related=True,
                confidence_score=0.5,
                matched_topics=['unknown'],
                relevant_documents=[],
                reason="Data analysis not available",
                coverage_gap=True
            )
        
        question_lower = question.lower().strip()
        
        # Calculate relevance based on actual data
        relevance_score = 0.0
        matched_topics = []
        relevant_documents = []
        
        # 1. Check against key topics from data
        for topic in self.data_analysis.key_topics:
            topic_keywords = self._get_topic_keywords(topic)
            for keyword in topic_keywords:
                if keyword in question_lower:
                    confidence = self.data_analysis.confidence_keywords.get(topic, 0.5)
                    relevance_score += confidence
                    matched_topics.append(topic)
                    relevant_documents.extend(self.topic_document_map.get(topic, []))
                    break
        
        # 2. Check against known entities
        for entity in self.data_analysis.trade_entities:
            if entity.lower() in question_lower:
                relevance_score += 0.8
                matched_topics.append(f"entity:{entity}")
        
        # 3. Calculate final classification
        total_words = len(question_lower.split())
        confidence_score = min(relevance_score / max(total_words, 1), 1.0)
        
        # More permissive classification - if any trade relevance found, allow it
        trade_indicators = ['trade', 'business', 'export', 'import', 'commercial', 'document', 'procedure', 'process', 'customs', 'duty']
        has_trade_indicators = any(indicator in question_lower for indicator in trade_indicators)
        
        is_data_related = (
            confidence_score > 0.05 or  # Very low threshold
            relevance_score > 0.3 or   # Any reasonable relevance
            has_trade_indicators       # Basic trade terms
        )
        coverage_gap = relevance_score == 0.0 and not has_trade_indicators
        
        reason = self._generate_classification_reason(matched_topics, confidence_score, coverage_gap)
        
        return TopicClassification(
            is_data_related=is_data_related,
            confidence_score=confidence_score,
            matched_topics=matched_topics,
            relevant_documents=list(set(relevant_documents[:5])),  # Top 5 relevant docs
            reason=reason,
            coverage_gap=coverage_gap
        )
    
    def _get_topic_keywords(self, topic: str) -> List[str]:
        """Get keywords for a topic based on data analysis"""
        keyword_map = {
            'dgft': ['dgft', 'foreign trade policy', 'directorate general'],
            'export': ['export', 'exporting', 'exporter', 'outbound'],
            'import': ['import', 'importing', 'importer', 'inbound'],
            'customs': ['customs', 'duty', 'tariff', 'clearance'],
            'certification': ['certificate', 'certification', 'license'],
            'valuation': ['valuation', 'value', 'assessment'],
            'classification': ['classification', 'hsn', 'code'],
            'schemes': ['scheme', 'incentive', 'promotion'],
            'compliance': ['compliance', 'regulation', 'policy'],
            'documentation': ['document', 'documentation', 'paperwork'],
            'logistics': ['logistics', 'transport', 'warehouse'],
            'dispute': ['dispute', 'appeal', 'grievance']
        }
        
        return keyword_map.get(topic, [topic.replace('_', ' ')])
    
    def _generate_classification_reason(self, matched_topics: List[str], confidence_score: float, coverage_gap: bool) -> str:
        """Generate classification reason"""
        if coverage_gap:
            return f"No relevant topics found in trade data (confidence: {confidence_score:.2f})"
        elif matched_topics:
            return f"Matched data topics: {', '.join(matched_topics[:3])} (confidence: {confidence_score:.2f})"
        else:
            return f"Low confidence match (score: {confidence_score:.2f})"
    
    def get_data_driven_redirect_response(self, question: str, classification: TopicClassification) -> str:
        """Generate redirect response based on actual data coverage"""
        if not self.data_analysis:
            return "I can help with trade-related questions based on my data."
        
        return f"""🚫 **Not a Trade-Related Question**

I'm a specialized **Trade Assistant** designed to help with import, export, and DGFT-related topics only.

Your question: "{question}" is outside my expertise area.

💼 **I can help you with:**
• Export-Import procedures
• DGFT schemes and policies  
• Customs clearance and documentation
• Trade compliance and certifications

🎯 **Try asking:**
• "How do I start an export business?"
• "What documents are needed for customs clearance?"
• "Explain DGFT export promotion schemes"

Please ask a trade-related question! 🌟"""
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of analyzed data for monitoring"""
        if not self.data_analysis:
            return {"status": "No analysis available"}
        
        return {
            "analysis_status": "completed",
            "total_documents": self.data_analysis.total_documents,
            "key_topics": self.data_analysis.key_topics,
            "trade_entities": list(self.data_analysis.trade_entities),
            "coverage_areas": self.data_analysis.coverage_areas,
            "document_categories": {k: len(v) for k, v in self.data_analysis.document_categories.items()},
            "confidence_keywords_count": len(self.data_analysis.confidence_keywords),
            "config_file": self.config_output_path
        }

# Global data-driven filter instance
data_driven_filter = DataDrivenTradeFilter()