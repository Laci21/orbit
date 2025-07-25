"""Tweet streaming service for the Ear-to-Ground agent."""

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aiohttp

from agents.ear_to_ground.card import AGENT_CARD

logger = logging.getLogger("orbit.ear_to_ground_agent.streaming_service")




class TweetStreamingService:
    """Service responsible for streaming crisis tweets and calling agents directly."""
    
    def __init__(self, transport, broadcast_topic: Optional[str]):
        self.transport = transport
        self.broadcast_topic = broadcast_topic
        self.tweet_file = os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweet_rate = float(os.getenv("TWEET_STREAM_RATE", "1.0"))
        self.tweets: List[Dict[str, Any]] = []
        self._is_running = False
        self.final_crisis_response: Optional[Dict[str, Any]] = None  # Store final response
        # Convert agent card to dict following Coffee AGNTCY pattern
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
        # Agent endpoints for direct A2A calls
        self.sentiment_analyst_endpoint = os.getenv("SENTIMENT_ANALYST_URL", "http://sentiment-analyst:9002")
        self.fact_checker_endpoint = os.getenv("FACT_CHECKER_URL", "http://fact-checker:9004")
        self.risk_score_endpoint = os.getenv("RISK_SCORE_URL", "http://risk-score:9003")
        self.press_secretary_endpoint = os.getenv("PRESS_SECRETARY_URL", "http://press-secretary:9006")
        
    async def start(self) -> None:
        """Start the tweet streaming service."""
        if self._is_running:
            logger.warning("Tweet streaming service is already running")
            return
            
        # Wait for server to fully initialize
        await asyncio.sleep(5)
        
        logger.info("Starting tweet streaming service...")
        self._is_running = True
        
        try:
            await self._load_tweets()
            await self._stream_tweets()
        except Exception as e:
            logger.error(f"Error in tweet streaming service: {e}")
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
        except UnicodeDecodeError as e:
            logger.error(f"Error reading tweet file encoding: {e}")
            raise
            
    def _validate_tweets(self) -> None:
        """Validate tweet data structure."""
        required_fields = {'id', 'text', 'author'}
        
        for i, tweet in enumerate(self.tweets):
            if not isinstance(tweet, dict):
                raise ValueError(f"Tweet {i} is not a dictionary")
                
            missing_fields = required_fields - set(tweet.keys())
            if missing_fields:
                raise ValueError(f"Tweet {i} missing required fields: {missing_fields}")
                
        logger.info(f"Validated {len(self.tweets)} tweets successfully")
            
    async def _stream_tweets(self) -> None:
        """Stream tweets via SLIM transport."""
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
        """Process a single tweet by calling agents directly via A2A."""
        crisis_id = tweet.get("id", "unknown")
        
        logger.info(f"Processing crisis: {crisis_id} from {tweet['author']}")
        
        # Call agents directly via A2A (no SLIM broadcasting)
        await self._call_agents_directly(tweet, crisis_id)
        
    async def _publish_completion(self) -> None:
        """Log stream completion (no SLIM broadcasting)."""
        logger.info("All crisis tweets have been processed - no broadcasts sent")
            
    async def _call_agents_directly(self, tweet: Dict[str, Any], crisis_id: str) -> None:
        """Call sentiment analyst and fact checker agents directly via A2A."""
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
        """Call the sentiment analyst agent directly via A2A following lungo pattern."""
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.sentiment_analyst_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Sentiment analyst called successfully for crisis {crisis_data['crisis_id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Sentiment analyst call failed: {response.status} - {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            logger.error("Sentiment analyst call timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling sentiment analyst: {e}")
            return {"error": str(e)}
    
    async def _call_fact_checker(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the fact checker agent directly via A2A following lungo pattern."""
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fact_checker_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Fact checker called successfully for crisis {crisis_data['crisis_id']}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Fact checker call failed: {response.status} - {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            logger.error("Fact checker call timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling fact checker: {e}")
            return {"error": str(e)}
    
    async def _call_risk_score(self, crisis_data: Dict[str, Any], sentiment_result: Dict[str, Any], fact_result: Dict[str, Any]) -> Dict[str, Any]:
        """Call the risk score agent with combined analysis data."""
        try:
            # Use the improved extractor for both analyses
            sentiment_analysis = self._extract_analysis_data(sentiment_result, 'sentiment_analysis')
            fact_analysis = self._extract_analysis_data(fact_result, 'fact_analysis')
            
            # Validate that we successfully extracted analysis data
            if not sentiment_analysis or not fact_analysis:
                logger.error(f"Failed to extract analysis data. Sentiment: {bool(sentiment_analysis)}, Fact: {bool(fact_analysis)}")
                logger.debug(f"Sentiment result structure: {type(sentiment_result)} - {list(sentiment_result.keys()) if isinstance(sentiment_result, dict) else 'not dict'}")
                logger.debug(f"Fact result structure: {type(fact_result)} - {list(fact_result.keys()) if isinstance(fact_result, dict) else 'not dict'}")
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
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.risk_score_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Risk Score called successfully for crisis {crisis_data.get('crisis_id', 'unknown')}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Risk Score call failed: {response.status} - {error_text}")
                        return {"error": f"HTTP {response.status}: {error_text}"}
                        
        except asyncio.TimeoutError:
            logger.error("Risk Score call timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Error calling Risk Score: {e}")
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
            
            # Make HTTP request to Press Secretary agent
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.press_secretary_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        press_response = await response.json()
                        logger.info(f"Press Secretary response generated for crisis {crisis_data.get('crisis_id', 'unknown')}")
                        return press_response
                    else:
                        error_text = await response.text()
                        logger.error(f"Press Secretary call failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Press Secretary agent: {e}")
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