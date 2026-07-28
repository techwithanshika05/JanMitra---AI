from app.checklists.enums import ChecklistItemSourceState, ChecklistItemType
from app.checklists.models import SavedChecklist
from app.checklists.schemas import ChecklistGuidance


class ChecklistGuidanceService:
    @staticmethod
    def build(
        checklist: SavedChecklist,
        *,
        reminders_consented: bool = False,
    ) -> ChecklistGuidance:
        current = [
            item
            for item in checklist.items
            if item.source_state
            not in {
                ChecklistItemSourceState.REMOVED.value,
                ChecklistItemSourceState.OUTDATED.value,
            }
        ]
        incomplete_required = [
            item for item in current if item.is_required and not item.is_completed
        ]
        missing_documents = [
            item.title
            for item in incomplete_required
            if item.item_type == ChecklistItemType.DOCUMENT.value
        ]
        next_steps = [item.title for item in incomplete_required[:3]]

        if checklist.language == "hi":
            summary = (
                f"आपकी चेकलिस्ट {checklist.progress_percentage:.0f}% पूरी है। "
                f"{len(incomplete_required)} आवश्यक कार्य बाकी हैं।"
            )
            explanations = [
                f"अगला आवश्यक कार्य: {item.title}" for item in incomplete_required[:3]
            ]
            alternatives = [
                f"यदि “{item.title}” पूरा नहीं हो पा रहा है, तो संबंधित आधिकारिक कार्यालय या हेल्पलाइन से स्वीकार्य विकल्प पूछें।"
                for item in incomplete_required[:2]
            ]
            reminders = (
                ["अपने अधूरे आवश्यक कार्यों की स्थिति जाँचने के लिए स्मरण रखें।"]
                if reminders_consented and incomplete_required
                else []
            )
        elif checklist.language == "hinglish":
            summary = (
                f"Aapki checklist {checklist.progress_percentage:.0f}% complete hai. "
                f"{len(incomplete_required)} required kaam baaki hain."
            )
            explanations = [
                f"Agla required kaam: {item.title}" for item in incomplete_required[:3]
            ]
            alternatives = [
                f"Agar “{item.title}” complete nahi ho raha, official office ya helpline se accepted alternative poochhein."
                for item in incomplete_required[:2]
            ]
            reminders = (
                ["Apne pending required steps ka status check karne ka reminder rakhein."]
                if reminders_consented and incomplete_required
                else []
            )
        else:
            summary = (
                f"Your checklist is {checklist.progress_percentage:.0f}% complete. "
                f"{len(incomplete_required)} required items remain."
            )
            explanations = [
                f"Next required item: {item.title}" for item in incomplete_required[:3]
            ]
            alternatives = [
                f"If “{item.title}” cannot be completed, ask the relevant official office or helpline which alternatives it accepts."
                for item in incomplete_required[:2]
            ]
            reminders = (
                ["Remember to review the status of your remaining required items."]
                if reminders_consented and incomplete_required
                else []
            )

        return ChecklistGuidance(
            progress_summary=summary,
            next_steps=next_steps,
            missing_documents=missing_documents,
            short_explanations=explanations,
            alternative_actions=alternatives,
            reminders=reminders,
        )
