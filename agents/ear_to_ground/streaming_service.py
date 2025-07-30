"""Tweet streaming service for crisis management."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles

from agents.ear_to_ground.card import AGENT_CARD
from common.slim_client import call_agent_slim

logger = logging.getLogger("orbit.ear_to_ground_agent.streaming_service")


class TweetStreamingService:
    """Service for streaming crisis tweets and coordinating agent responses."""
    
    def __init__(self, tweet_file: Optional[str] = None, tweet_rate: Optional[float] = None):
        # Set default tweet file and rate
        self.tweet_file = tweet_file or os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweet_rate = tweet_rate or 2.0  # seconds between tweets
        
        # Internal state
        self.tweets: List[Dict[str, Any]] = []
        self._is_running = False
        self.final_crisis_response: Optional[Dict[str, Any]] = None  # Store final response
        # Convert agent card to dict following Coffee AGNTCY pattern
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
        # Agent progress tracking
        self.agent_progress: Dict[str, str] = {
            'ear_to_ground': 'idle',
            'sentiment_analyst': 'idle', 
            'fact_checker': 'idle',
            'risk_score': 'idle',
            'legal_counsel': 'idle',
            'press_secretary': 'idle'
        }
        
        # Agent results storage
        self.agent_results: Dict[str, Dict[str, Any]] = {}
        
        # Agent endpoints for SLIM communication
        self.sentiment_analyst_endpoint = os.getenv("SENTIMENT_ANALYST_URL", "slim://sentiment-analyst:50052")
        self.fact_checker_endpoint = os.getenv("FACT_CHECKER_URL", "slim://fact-checker:50053")
        self.risk_score_endpoint = os.getenv("RISK_SCORE_URL", "slim://risk-score:50054")
        self.press_secretary_endpoint = os.getenv("PRESS_SECRETARY_URL", "slim://press-secretary:50056")
    
    def set_agent_status(self, agent_id: str, status: str) -> None:
        """Set agent status for progress tracking."""
        if agent_id in self.agent_progress:
            self.agent_progress[agent_id] = status
            logger.info(f"Agent {agent_id} status: {status}")
        else:
            logger.warning(f"Unknown agent ID: {agent_id}")
    
    def set_agent_result(self, agent_id: str, result: Dict[str, Any]) -> None:
        """Store agent result data."""
        self.agent_results[agent_id] = result
        logger.info(f"Agent {agent_id} result stored")
    
    def get_progress(self) -> Dict[str, str]:
        """Get current agent progress states."""
        return self.agent_progress.copy()
    
    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent results."""
        return self.agent_results.copy()
    
    def reset_agents(self) -> None:
        """Reset all agents to idle state for new crisis."""
        for agent_id in self.agent_progress:
            self.agent_progress[agent_id] = 'idle'
        self.agent_results.clear()
        logger.info("All agents reset to idle state")
        
    async def start(self) -> None:
        """Start the tweet streaming service."""
        if self._is_running:
            logger.warning("Tweet streaming service is already running")
            return
            
        # Reset agents and set ear-to-ground as active
        self.reset_agents()
        self.set_agent_status('ear_to_ground', 'active')
            
        # Wait for server to fully initialize
        await asyncio.sleep(5)
        
        logger.info("Starting tweet streaming service...")
        self._is_running = True
        
        try:
            await self._load_tweets()
            await self._stream_tweets()
            self.set_agent_status('ear_to_ground', 'complete')
        except Exception as e:
            logger.error(f"Error in tweet streaming service: {e}")
            self.set_agent_status('ear_to_ground', 'error')
            raise
        finally:
            self._is_running = False
            
    async def _load_tweets(self) -> None:
        """Load tweets from JSON file asynchronously."""
        tweet_path = Path(self.tweet_file)
        
        if not tweet_path.exists():
            logger.error(f"Tweet file not found: {self.tweet_file}")
            raise FileNotFoundError(f"Tweet file not found: {self.tweet_file}")
            
        try:
            async with aiofiles.open(tweet_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                self.tweets = json.loads(content)
                
            logger.info(f"Loaded {len(self.tweets)} tweets for streaming")
            
            # Validate tweet structure
            self._validate_tweets()
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing tweet file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading tweets: {e}")
            raise
    
    def _validate_tweets(self) -> None:
        """Validate tweet structure."""
        if not self.tweets:
            raise ValueError("No tweets found in file")
            
        required_fields = ['id', 'author', 'text', 'timestamp']
        for i, tweet in enumerate(self.tweets):
            for field in required_fields:
                if field not in tweet:
                    raise ValueError(f"Tweet {i} missing required field: {field}")
        
        logger.info("Tweet validation passed")
    
    async def _stream_tweets(self) -> None:
        """Stream tweets and trigger crisis analysis."""
        logger.info(f"Processing {len(self.tweets)} tweets for crisis analysis...")
        
        # Process only the first tweet for now to ensure clean flow
        if not self.tweets:
            logger.warning("No tweets available to process")
            return
            
        tweet = self.tweets[0]  # Process only the first tweet
        logger.info(f"Processing single tweet for crisis demo: {tweet.get('id', 'unknown')}")
        
        try:
            await self._publish_tweet(tweet)
        except Exception as e:
            logger.error(f"Error processing tweet {tweet.get('id', 'unknown')}: {e}")
            
        # Original multi-tweet processing (commented out for now)
        # for tweet in self.tweets:
        #     if not self._is_running:
        #         break
        #         
        #     try:
        #         await self._publish_tweet(tweet)
        #         
        #         # Variable delay between tweets (0.8x to 1.5x base rate) 
        #         delay = self.tweet_rate * random.uniform(0.8, 1.5)
        #         await asyncio.sleep(delay)
        #         
        #     except Exception as e:
        #         logger.error(f"Error broadcasting tweet {tweet.get('id', 'unknown')}: {e}")
        #         continue
        
        await self._publish_completion()
        logger.info("Single tweet processing completed successfully")
        
    async def _publish_tweet(self, tweet: Dict[str, Any]) -> None:
        """Process a single tweet by calling agents directly via SLIM."""
        crisis_id = tweet.get("id", "unknown")
        
        logger.info(f"Processing crisis: {crisis_id} from {tweet['author']}")
        
        # Call agents directly via SLIM (no SLIM broadcasting)
        await self._call_agents_directly(tweet, crisis_id)
        
    async def _publish_completion(self) -> None:
        """Log stream completion (no SLIM broadcasting)."""
        logger.info("All crisis tweets have been processed - no broadcasts sent")
            
    async def _call_agents_directly(self, tweet: Dict[str, Any], crisis_id: str) -> None:
        """Call sentiment analyst and fact checker agents directly via SLIM."""
        try:
            # Prepare crisis data for analysis
            crisis_data = {
                "crisis_id": crisis_id,
                "text": tweet.get("text", ""),
                "content": tweet.get("text", ""),  # Fallback field name
                "author": tweet.get("author", ""),
                "timestamp": tweet.get("timestamp", ""),
                "source": "social_media",
                "platform": "twitter"
            }
            
            # Create tasks to call both agents in parallel
            tasks = []
            
            # Call sentiment analyst
            sentiment_task = asyncio.create_task(
                self._call_sentiment_analyst(crisis_data)
            )
            tasks.append(sentiment_task)
            
            # Call fact checker
            fact_checker_task = asyncio.create_task(
                self._call_fact_checker(crisis_data)
            )
            tasks.append(fact_checker_task)
            
            # Wait for both agent calls to complete with 30s timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0
                )
                
                # Process results and call Risk Score if both succeeded
                sentiment_result = None
                fact_result = None
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Agent call {i} failed: {result}")
                    else:
                        logger.info(f"Agent call {i} completed successfully")
                        # Extract analysis data from successful results
                        if i == 0:  # Sentiment analyst
                            sentiment_result = result
                        elif i == 1:  # Fact checker
                            fact_result = result
                
                # Call Risk Score if both analyses completed
                if sentiment_result is not None and fact_result is not None:
                    risk_result = await self._call_risk_score(crisis_data, sentiment_result, fact_result)
                    
                    # Extract legal counsel data from fact result (fact checker calls legal counsel)
                    # Use the same recursive extractor as for other analysis data
                    legal_result = self._extract_analysis_data(fact_result, 'legal_review')
                    if not legal_result:
                        logger.debug("Legal review not found in fact checker response, trying alternative extraction")
                        legal_result = self._extract_legal_counsel_data(fact_result)
                    
                    # Call Press Secretary with all data if risk assessment succeeded
                    if risk_result is not None and legal_result is not None:
                        press_response = await self._call_press_secretary(crisis_data, sentiment_result, fact_result, risk_result, legal_result)
                        if press_response:
                            # Store the final response for retrieval by gateway
                            logger.info("Storing final Press Secretary response for gateway retrieval")
                            self.final_crisis_response = press_response
                            self._display_final_crisis_response(crisis_data, press_response)
                    else:
                        logger.error(f"Cannot call Press Secretary - missing data. Risk: {risk_result is not None}, Legal: {legal_result is not None}")
                else:
                    logger.error(f"Cannot call Risk Score - missing analysis data. Sentiment: {sentiment_result is not None}, Fact: {fact_result is not None}")
                    
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for fact checking and sentiment analysis to complete (30s)")
                # Continue without calling Risk Score
                    
        except Exception as e:
            logger.error(f"Error calling agents directly: {e}")
    
    async def _call_sentiment_analyst(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the sentiment analyst agent directly via SLIM following lungo pattern."""
        self.set_agent_status('sentiment_analyst', 'active')
        
        try:
            # Simple prompt with crisis content (following lungo pattern)
            prompt = f"Please analyze the sentiment of this crisis content: {crisis_data['text']}"
            
            # JSON-RPC request payload for A2A communication
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"crisis-{crisis_data['crisis_id']}-sentiment",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            # Call sentiment analyst via SLIM
            result = await call_agent_slim(
                self.sentiment_analyst_endpoint,
                request_payload,
                timeout=30.0
            )
            
            if "error" not in result:
                logger.info(f"Sentiment analyst called successfully for crisis {crisis_data['crisis_id']}")
                
                # Extract and store sentiment analysis result
                sentiment_analysis = self._extract_analysis_data(result, 'sentiment_analysis')
                if sentiment_analysis:
                    self.set_agent_result('sentiment_analyst', sentiment_analysis)
                
                self.set_agent_status('sentiment_analyst', 'complete')
                return result
            else:
                logger.error(f"Sentiment analyst call failed via SLIM: {result.get('error', 'Unknown error')}")
                self.set_agent_status('sentiment_analyst', 'error')
                return {"error": result.get("error", "Unknown error")}
                        
        except Exception as e:
            logger.error(f"Error calling sentiment analyst via SLIM: {e}")
            self.set_agent_status('sentiment_analyst', 'error')
            return {"error": str(e)}
    
    async def _call_fact_checker(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the fact checker agent directly via SLIM following lungo pattern."""
        self.set_agent_status('fact_checker', 'active')
        # Legal counsel will be called by fact checker, so mark it as active too
        self.set_agent_status('legal_counsel', 'active')
        
        try:
            # Simple prompt with crisis content for fact checking
            prompt = f"Please verify the claims in this crisis content: {crisis_data['text']}"
            
            # JSON-RPC request payload for A2A communication
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"crisis-{crisis_data['crisis_id']}-factcheck",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            # Call fact checker via SLIM
            result = await call_agent_slim(
                self.fact_checker_endpoint,
                request_payload,
                timeout=30.0
            )
            
            if "error" not in result:
                logger.info(f"Fact checker called successfully for crisis {crisis_data['crisis_id']}")
                
                # Extract and store fact check analysis result
                fact_analysis = self._extract_analysis_data(result, 'fact_check')
                if fact_analysis:
                    self.set_agent_result('fact_checker', fact_analysis)
                
                # Also check for legal review data and store it
                legal_review = self._extract_analysis_data(result, 'legal_review')
                if legal_review:
                    self.set_agent_result('legal_counsel', legal_review)
                    self.set_agent_status('legal_counsel', 'complete')
                
                self.set_agent_status('fact_checker', 'complete')
                return result
            else:
                logger.error(f"Fact checker call failed via SLIM: {result.get('error', 'Unknown error')}")
                self.set_agent_status('fact_checker', 'error')
                self.set_agent_status('legal_counsel', 'error')
                return {"error": result.get("error", "Unknown error")}
                
        except Exception as e:
            logger.error(f"Error calling fact checker via SLIM: {e}")
            self.set_agent_status('fact_checker', 'error')
            self.set_agent_status('legal_counsel', 'error')
            return {"error": str(e)}
    
    async def _call_risk_score(self, crisis_data: Dict[str, Any], sentiment_result: Dict[str, Any], fact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Call the risk score agent with combined analysis data."""
        self.set_agent_status('risk_score', 'active')
        
        try:
            # Use the improved extractor for both analyses
            sentiment_analysis = self._extract_analysis_data(sentiment_result, 'sentiment_analysis')
            fact_analysis = self._extract_analysis_data(fact_result, 'fact_check_analysis')
            
            # Validate that we successfully extracted analysis data
            if not sentiment_analysis or not fact_analysis:
                logger.error(f"Failed to extract analysis data. Sentiment: {bool(sentiment_analysis)}, Fact: {bool(fact_analysis)}")
                # Detailed structures no longer logged to reduce noise
                return {"error": "Failed to extract analysis data from agent responses"}
            
            # Prepare combined analysis data for Risk Score
            combined_analysis = {
                "crisis_id": crisis_data.get("crisis_id", "unknown"),
                "fact_analysis": fact_analysis,
                "sentiment_analysis": sentiment_analysis,
                "timestamp": crisis_data.get("timestamp", ""),
                "content": crisis_data.get("text", "")
            }
            
            logger.info(f"Successfully extracted analysis data for crisis {crisis_data.get('crisis_id', 'unknown')}: fact_credibility={fact_analysis.get('overall_credibility', 'unknown')}, sentiment_score={sentiment_analysis.get('overall_sentiment', 'unknown')}")
            
            # Create prompt for Risk Score agent
            prompt = f"Please assess the risk for this crisis with combined analysis: {json.dumps(combined_analysis)}"
            
            # JSON-RPC request payload for Risk Score
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"risk-assessment-{crisis_data.get('crisis_id', 'unknown')}",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            # Call Risk Score via SLIM
            result = await call_agent_slim(
                self.risk_score_endpoint,
                request_payload,
                timeout=30.0
            )

            # Check if result is dict and has no error
            if isinstance(result, dict) and "error" not in result:
                logger.info(f"Risk Score called successfully for crisis {crisis_data.get('crisis_id', 'unknown')}")
                
                # Extract and store risk analysis result
                risk_analysis = self._extract_analysis_data(result, 'risk_assessment')
                if risk_analysis:
                    self.set_agent_result('risk_score', risk_analysis)
                
                self.set_agent_status('risk_score', 'complete')
                return result
            else:
                # Handle both dict and string error responses
                if isinstance(result, dict):
                    error_msg = result.get('error', 'Unknown error')
                else:
                    error_msg = str(result)
                logger.error(f"Risk Score call failed via SLIM: {error_msg}")
                self.set_agent_status('risk_score', 'error')
                return {"error": error_msg}
                        
        except Exception as e:
            logger.error(f"Error calling Risk Score: {e}")
            self.set_agent_status('risk_score', 'error')
            return {"error": str(e)}
    
    def _extract_legal_counsel_data(self, fact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract legal counsel data from fact checker response (fact checker calls legal counsel)."""
        try:
            # Attempt to extract using the generic recursive extractor first
            legal_review = self._extract_analysis_data(fact_result, 'legal_review')
            if legal_review:
                logger.info("Successfully extracted legal counsel review from fact checker result")
                return legal_review

            # Fallback to previous structured path for backward-compatibility
            if isinstance(fact_result, dict):
                if 'result' in fact_result and isinstance(fact_result['result'], dict):
                    result_data = fact_result['result']
                    if 'metadata' in result_data:
                        metadata = result_data['metadata']
                        if 'legal_review' in metadata:
                            return metadata['legal_review']

            # If still not found, log and return None so caller can decide how to proceed
            logger.debug("Legal review not found in fact checker response")
            return None
         
        except Exception as e:
            logger.error(f"Error extracting legal counsel data: {e}")
            return None
    
    async def _call_press_secretary(self, crisis_data: Dict[str, Any], sentiment_result: Dict[str, Any], 
                                  fact_result: Dict[str, Any], risk_result: Dict[str, Any], 
                                  legal_result: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Press Secretary agent with all comprehensive crisis analysis data."""
        self.set_agent_status('press_secretary', 'active')
        
        try:
            # Extract analysis data from each agent response
            sentiment_analysis = self._extract_analysis_data(sentiment_result, 'sentiment_analysis')
            fact_analysis = self._extract_analysis_data(fact_result, 'fact_analysis') 
            risk_assessment = self._extract_analysis_data(risk_result, 'risk_assessment')
            
            # Prepare comprehensive crisis data package for Press Secretary
            comprehensive_data = {
                "crisis_id": crisis_data.get("crisis_id", "unknown"),
                "crisis_data": crisis_data,
                "sentiment_analysis": sentiment_analysis,
                "fact_analysis": fact_analysis,
                "risk_assessment": risk_assessment,
                "legal_review": legal_result,
                "timestamp": crisis_data.get("timestamp", "")
            }
            
            # Create prompt for Press Secretary
            prompt = f"""Please generate official crisis response based on comprehensive analysis.

CRISIS_DATA:
{json.dumps(comprehensive_data, indent=2)}
END_CRISIS_DATA"""
            
            # JSON-RPC request payload for Press Secretary
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"press-response-{crisis_data.get('crisis_id', 'unknown')}",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            # Call Press Secretary via SLIM
            result = await call_agent_slim(
                self.press_secretary_endpoint,
                request_payload,
                timeout=30.0
            )

            if "error" not in result:
                logger.info(f"Press Secretary response generated for crisis {crisis_data.get('crisis_id', 'unknown')}")
                
                # Extract and store press secretary result
                press_analysis = self._extract_analysis_data(result, 'press_response')
                if press_analysis:
                    self.set_agent_result('press_secretary', press_analysis)
                
                self.set_agent_status('press_secretary', 'complete')
                return result
            else:
                logger.error(f"Press Secretary call failed via SLIM: {result.get('error', 'Unknown error')}")
                self.set_agent_status('press_secretary', 'error')
                return None
                        
        except Exception as e:
            logger.error(f"Error calling Press Secretary agent: {e}")
            self.set_agent_status('press_secretary', 'error')
            return None
    
    def _extract_analysis_data(self, agent_result: Dict[str, Any], analysis_key: str) -> Dict[str, Any]:
        """Extract analysis data from agent response."""
        try:
            if not agent_result:
                return {}

            # Helper to look for metadata recursively
            def _search(node: Any) -> Optional[Dict[str, Any]]:
                if isinstance(node, dict):
                    # Direct hit
                    if analysis_key in node:
                        return node[analysis_key]
                    # Metadata path
                    if 'metadata' in node and isinstance(node['metadata'], dict) and analysis_key in node['metadata']:
                        return node['metadata'][analysis_key]
                    # Recurse on dict values
                    for v in node.values():
                        found = _search(v)
                        if found is not None:
                            return found
                elif isinstance(node, list):
                    for item in node:
                        found = _search(item)
                        if found is not None:
                            return found
                return None

            found_data = _search(agent_result)
            if found_data is None:
                logger.debug(f"Could not extract {analysis_key} from agent result")
                return {}
            return found_data
        except Exception as e:
            logger.error(f"Error extracting {analysis_key}: {e}")
            return {}

    def stop(self) -> None:
        """Stop the streaming service."""
        self._is_running = False
        logger.info("Tweet streaming service stopped")

    def _display_final_crisis_response(self, crisis_data: Dict[str, Any], press_response: Dict[str, Any]) -> None:
        """Display the final crisis response in a nicely formatted way."""
        try:
            crisis_id = crisis_data.get('crisis_id', 'unknown')
            
            # Extract the press response from the JSON-RPC envelope
            final_response = None
            if isinstance(press_response, dict) and 'result' in press_response:
                result = press_response['result']
                if isinstance(result, dict) and 'metadata' in result:
                    final_response = result['metadata'].get('press_response')
            
            if final_response and isinstance(final_response, dict):
                logger.info("=" * 80)
                logger.info(f"🎯 FINAL CRISIS RESPONSE - Crisis ID: {crisis_id}")
                logger.info("=" * 80)
                
                # Primary statement
                primary = final_response.get('primary_statement', 'No statement available')
                logger.info(f"📢 PRIMARY STATEMENT ({final_response.get('tone', 'unknown')} tone):")
                logger.info(f"   {primary}")
                logger.info("")
                
                # Key messages
                key_messages = final_response.get('key_messages', [])
                if key_messages:
                    logger.info("🔑 KEY MESSAGES:")
                    for i, msg in enumerate(key_messages, 1):
                        logger.info(f"   {i}. {msg}")
                    logger.info("")
                
                # Channel-specific responses
                channels = final_response.get('channels', {})
                if channels:
                    logger.info("📺 CHANNEL-SPECIFIC RESPONSES:")
                    if 'press_release' in channels:
                        logger.info(f"   📰 Press Release: {channels['press_release'][:100]}...")
                    if 'social_media' in channels:
                        logger.info(f"   📱 Social Media: {channels['social_media']}")
                    if 'employee_memo' in channels:
                        logger.info(f"   👥 Employee Memo: {channels['employee_memo'][:100]}...")
                    logger.info("")
                
                # Risk assessment
                reputational_risk = final_response.get('reputational_risk', 'unknown')
                confidence = final_response.get('confidence', 0.0)
                legal_compliance = final_response.get('legal_compliance', False)
                
                logger.info(f"⚖️  COMPLIANCE: {'✅ Legal compliant' if legal_compliance else '❌ Legal concerns'}")
                logger.info(f"🎯 CONFIDENCE: {confidence:.1%}")
                logger.info(f"📊 REPUTATIONAL RISK: {reputational_risk.upper()}")
                
                logger.info("=" * 80)
                logger.info("✅ Crisis response generation completed successfully!")
                logger.info("=" * 80)
            else:
                logger.warning("Could not extract final crisis response from Press Secretary")
                logger.info(f"🎯 Crisis response generated for crisis {crisis_id} (details not parsed)")
                
        except Exception as e:
            logger.error(f"Error displaying final crisis response: {e}")
            logger.info(f"🎯 Crisis response generated for crisis {crisis_data.get('crisis_id', 'unknown')}")

    def get_final_response(self) -> Optional[Dict[str, Any]]:
        """Get the final crisis response for external consumption (e.g., by gateway)."""
        return self.final_crisis_response

    def clear_final_response(self) -> None:
        """Clear the stored final response (for new crises)."""
        logger.info("Clearing previous final response for new crisis")
        self.final_crisis_response = None
        self.reset_agents()