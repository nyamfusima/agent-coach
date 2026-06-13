# Billing — Overview (call flow)

**Systems used:** Carehub, Smart Agent

1. [Smart Agent] Auto Answer
2. [Smart Agent] Whisper with Query Type
3. [Carehub] Capture name
4. [Carehub] Paste number
5. [Smart Agent] Copy Number
6. [Carehub] Clear Spaces in copied number
7. [Carehub] Click Next
8. [Carehub] Select account holder
9. [Carehub] Select reason for call from level 1
10. [Carehub] From level 1 selection, level 2 selection is selected
11. From level 2 selection, level 3 selection is selected
12. [Carehub] Select method to send Otac
13. [Carehub] Select next
14. [Carehub] Wait for customer to repeat Otac
15. [Carehub] Enter Otac from customer and click next
16. [Smart Agent] Inform customer DPA has failed and end call
17. **Decision — [Carehub] DPA passed?**
   - If **YES**: Open Account
   - If **NO**: Inform customer DPA has failed and end call
18. [Smart Agent] ACW (10 sec)
   - (end of this flow)
19. [Carehub] Open Account
20. [Carehub] Leave Detailed Notes/ DPA result
21. [Carehub] Select Level 4 Disposition
22. [Carehub] Close Account
23. Close Account
   - (end of this flow)

## Options / query types
- Credit Transfers
- Anytime Upgrade
- Debt Recovery
- Inclusive allowance
- Safety buffer / High Usage
- Treatment
- VAT

## Notes
- Steps to Triage calls (Find the correct process to use)
- OTAC is the OTP used as a security pin
