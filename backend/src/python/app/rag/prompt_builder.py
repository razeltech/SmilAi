from .prompts import SMILEY_SYSTEM_PROMPT

class PromptBuilder:
    def __init__(self):
        self.system_prompt = SMILEY_SYSTEM_PROMPT

    def build_persona(self) -> dict:
        """Returns the base Smiley persona system prompt message."""
        return {"role": "system", "content": self.system_prompt}

    def build_student_memory(self, profile_card: str) -> list:
        """Returns student memory system block if a profile card is provided."""
        if profile_card and profile_card.strip():
            return [{"role": "system", "content": profile_card.strip()}]
        return []

    def build_history(self, history: list) -> list:
        """Constructs list of system/user messages representing session history."""
        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        return messages

    def build_user_message(self, query: str, retrieved_chunks: list, is_conversational: bool) -> dict:
        """Assembles context details and query into the final user request message."""
        if is_conversational:
            user_content = f"""Student's Chat/Greeting/Concern: {query}
        
Please respond to the student warmly, naturally, and encourage them to learn. 
You can chat casually, offer support, answer general check-in questions, and help them transition into their studies.
Do NOT reference textbooks, syllabus, search results, or context files. Keep it motherly, gentle, and encouraging.

CRITICAL CONSTRAINT: Do NOT use any emojis or emoticons (like 😊, 🌟, :-)) in your reply under any circumstances."""
        else:
            if retrieved_chunks:
                context_blocks = []
                for i, chunk in enumerate(retrieved_chunks, start=1):
                    source_name = chunk.get("source", "Syllabus Resource")
                    context_blocks.append(f"Passage [{i}] (Source: {source_name})\n{chunk['text']}")
                context_text = "\n\n".join(context_blocks)
            else:
                context_text = "(No syllabus documents are available or relevant to this question. Please answer using general educational knowledge, indicating that it goes beyond the syllabus.)"
                
            user_content = f"""Syllabus Context Information:
{context_text}

Student's Question: {query}

Using the syllabus context above as your primary reference, answer the student's question according to your teaching guidelines.

CRITICAL CONSTRAINT: Do NOT use any emojis or emoticons (like 😊, 🌟, :-)) in your reply under any circumstances."""
            
        return {"role": "user", "content": user_content}

    def build(
        self,
        query: str,
        retrieved_chunks: list,
        history: list = None,
        is_conversational: bool = False,
        profile_card: str = ""
    ) -> list:
        """Composes all modular prompt segments into a structured messages payload."""
        messages = []
        
        # 1. Base identity persona
        messages.append(self.build_persona())
        
        # 2. Student memory card
        messages.extend(self.build_student_memory(profile_card))
        
        # 3. Conversation history
        messages.extend(self.build_history(history))
        
        # 4. User request context
        messages.append(self.build_user_message(query, retrieved_chunks, is_conversational))
        
        return messages

# Global singleton instance for clean reuse across request endpoints
PROMPT_BUILDER = PromptBuilder()
