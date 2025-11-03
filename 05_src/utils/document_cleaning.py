"""
Document cleaning utilities for PDF text preprocessing.

This module provides functions to clean and normalize text extracted from PDFs
before processing with LLMs.
"""

import re

try:
    import tiktoken
    TOKENIZER_AVAILABLE = True
except ImportError:
    TOKENIZER_AVAILABLE = False


def clean_document_text(text):
    """
    Clean and normalize document text for LLM processing.
    
    This function applies basic data cleaning techniques to prepare PDF-extracted
    text for optimal LLM processing. It handles common issues like encoding errors,
    excessive whitespace, and improper line breaks.
    
    Args:
        text (str): Raw document text extracted from PDF
        
    Returns:
        str: Cleaned and normalized text ready for LLM processing
    """
    # Step 1: Handle encoding issues gracefully
    # Remove or replace problematic characters that may cause encoding errors
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    
    # Handle common encoding issues by removing problematic unicode characters
    text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    
    # Step 2: Normalize line breaks - preserve paragraph breaks but join broken sentences
    # Replace double newlines (paragraph breaks) with a temporary marker
    text = text.replace('\n\n', '|||PARAGRAPH_BREAK|||')
    # Replace single newlines with spaces (these are likely broken sentences)
    text = text.replace('\n', ' ')
    # Restore paragraph breaks
    text = text.replace('|||PARAGRAPH_BREAK|||', '\n\n')
    
    # Step 3: Normalize whitespace
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    # Replace multiple consecutive spaces with a single space
    text = re.sub(r' +', ' ', text)
    
    # Step 4: Clean up hyphenated line breaks (common in PDFs)
    # Fix words broken across lines with hyphens followed by space (e.g., "word- \nword" -> "wordword")
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    
    # Step 5: Remove leading and trailing whitespace from each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Step 6: Remove excessive blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Step 7: Final trim of leading/trailing whitespace
    text = text.strip()
    
    return text


def count_tokens(text, model="gpt-4o-mini"):
    """
    Count tokens in text using tiktoken if available, otherwise approximate.
    
    Args:
        text (str): Text to count tokens for
        model (str): Model name for tokenizer (default: gpt-4o-mini)
        
    Returns:
        int: Approximate token count
    """
    if TOKENIZER_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            # Fallback to word-based approximation
            return len(text.split()) // 0.75  # Rough approximation: ~0.75 words per token
    else:
        # Simple approximation: average English word is ~1.3 tokens
        return int(len(text.split()) * 1.3)


def evaluate_cleaning(original_text, cleaned_text):
    """
    Evaluate the effectiveness of document cleaning by comparing original vs cleaned text.
    
    This function computes quantitative metrics including text statistics, whitespace
    reduction, and token efficiency to demonstrate cleaning effectiveness.
    
    Args:
        original_text (str): Original text before cleaning
        cleaned_text (str): Text after cleaning
        
    Returns:
        dict: Dictionary containing all evaluation metrics
    """
    # Helper function to count patterns
    def count_pattern(text, pattern):
        return len(re.findall(pattern, text))
    
    # Helper function to count_multiple_spaces
    def count_multiple_spaces(text):
        return len(re.findall(r' {2,}', text))
    
    # Calculate text statistics
    metrics = {
        'original': {},
        'cleaned': {},
        'improvements': {}
    }
    
    # Character and word counts
    metrics['original']['char_count'] = len(original_text)
    metrics['cleaned']['char_count'] = len(cleaned_text)
    metrics['improvements']['char_reduction'] = metrics['original']['char_count'] - metrics['cleaned']['char_count']
    metrics['improvements']['char_reduction_pct'] = (metrics['improvements']['char_reduction'] / metrics['original']['char_count'] * 100) if metrics['original']['char_count'] > 0 else 0
    
    metrics['original']['word_count'] = len(original_text.split())
    metrics['cleaned']['word_count'] = len(cleaned_text.split())
    
    # Whitespace metrics
    metrics['original']['spaces'] = original_text.count(' ')
    metrics['cleaned']['spaces'] = cleaned_text.count(' ')
    
    metrics['original']['tabs'] = original_text.count('\t')
    metrics['cleaned']['tabs'] = cleaned_text.count('\t')
    
    metrics['original']['newlines'] = original_text.count('\n')
    metrics['cleaned']['newlines'] = cleaned_text.count('\n')
    
    metrics['original']['multiple_spaces'] = count_multiple_spaces(original_text)
    metrics['cleaned']['multiple_spaces'] = count_multiple_spaces(cleaned_text)
    
    # Count excessive blank lines (>2 consecutive)
    metrics['original']['excessive_blank_lines'] = count_pattern(original_text, r'\n{3,}')
    metrics['cleaned']['excessive_blank_lines'] = count_pattern(cleaned_text, r'\n{3,}')
    
    # Count single newlines (likely broken sentences)
    single_newlines_original = count_pattern(original_text, r'(?<!\n)\n(?!\n)')
    single_newlines_cleaned = count_pattern(cleaned_text, r'(?<!\n)\n(?!\n)')
    metrics['original']['single_newlines'] = single_newlines_original
    metrics['cleaned']['single_newlines'] = single_newlines_cleaned
    
    # Text density (non-whitespace ratio)
    metrics['original']['text_density'] = len(re.sub(r'\s', '', original_text)) / len(original_text) if len(original_text) > 0 else 0
    metrics['cleaned']['text_density'] = len(re.sub(r'\s', '', cleaned_text)) / len(cleaned_text) if len(cleaned_text) > 0 else 0
    
    # Sentence count (approximate)
    metrics['original']['sentence_count'] = len(re.findall(r'[.!?]+', original_text))
    metrics['cleaned']['sentence_count'] = len(re.findall(r'[.!?]+', cleaned_text))
    
    # Average words per sentence
    metrics['original']['avg_words_per_sentence'] = metrics['original']['word_count'] / metrics['original']['sentence_count'] if metrics['original']['sentence_count'] > 0 else 0
    metrics['cleaned']['avg_words_per_sentence'] = metrics['cleaned']['word_count'] / metrics['cleaned']['sentence_count'] if metrics['cleaned']['sentence_count'] > 0 else 0
    
    # Token counts
    metrics['original']['token_count'] = count_tokens(original_text)
    metrics['cleaned']['token_count'] = count_tokens(cleaned_text)
    metrics['improvements']['token_reduction'] = metrics['original']['token_count'] - metrics['cleaned']['token_count']
    metrics['improvements']['token_reduction_pct'] = (metrics['improvements']['token_reduction'] / metrics['original']['token_count'] * 100) if metrics['original']['token_count'] > 0 else 0
    
    # Calculate improvements
    metrics['improvements']['spaces_reduced'] = metrics['original']['spaces'] - metrics['cleaned']['spaces']
    metrics['improvements']['tabs_removed'] = metrics['original']['tabs'] - metrics['cleaned']['tabs']
    metrics['improvements']['single_newlines_fixed'] = metrics['original']['single_newlines'] - metrics['cleaned']['single_newlines']
    metrics['improvements']['multiple_spaces_reduced'] = metrics['original']['multiple_spaces'] - metrics['cleaned']['multiple_spaces']
    metrics['improvements']['excessive_blank_lines_removed'] = metrics['original']['excessive_blank_lines'] - metrics['cleaned']['excessive_blank_lines']
    
    return metrics


def print_evaluation_report(metrics):
    """
    Print a formatted evaluation report showing cleaning effectiveness.
    
    Args:
        metrics (dict): Metrics dictionary from evaluate_cleaning()
    """
    print("=" * 80)
    print("DOCUMENT CLEANING EVALUATION REPORT")
    print("=" * 80)
    print()
    
    # Text Statistics
    print("📊 TEXT STATISTICS")
    print("-" * 80)
    print(f"Character Count:")
    print(f"  Original: {metrics['original']['char_count']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['char_count']:,}")
    print(f"  Reduction: {metrics['improvements']['char_reduction']:,} ({metrics['improvements']['char_reduction_pct']:.2f}%)")
    print()
    
    print(f"Word Count:")
    print(f"  Original: {metrics['original']['word_count']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['word_count']:,}")
    print()
    
    print(f"Sentence Count:")
    print(f"  Original: {metrics['original']['sentence_count']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['sentence_count']:,}")
    print()
    
    print(f"Average Words per Sentence:")
    print(f"  Original: {metrics['original']['avg_words_per_sentence']:.2f}")
    print(f"  Cleaned:  {metrics['cleaned']['avg_words_per_sentence']:.2f}")
    print()
    
    # Whitespace Metrics
    print("🔤 WHITESPACE METRICS")
    print("-" * 80)
    print(f"Spaces:")
    print(f"  Original: {metrics['original']['spaces']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['spaces']:,}")
    print(f"  Reduced:  {metrics['improvements']['spaces_reduced']:,}")
    print()
    
    print(f"Multiple Consecutive Spaces:")
    print(f"  Original: {metrics['original']['multiple_spaces']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['multiple_spaces']:,}")
    print(f"  Reduced:  {metrics['improvements']['multiple_spaces_reduced']:,}")
    print()
    
    print(f"Tab Characters:")
    print(f"  Original: {metrics['original']['tabs']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['tabs']:,}")
    print(f"  Removed:  {metrics['improvements']['tabs_removed']:,}")
    print()
    
    print(f"Single Newlines (broken sentences):")
    print(f"  Original: {metrics['original']['single_newlines']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['single_newlines']:,}")
    print(f"  Fixed:    {metrics['improvements']['single_newlines_fixed']:,}")
    print()
    
    print(f"Excessive Blank Lines (>2 consecutive):")
    print(f"  Original: {metrics['original']['excessive_blank_lines']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['excessive_blank_lines']:,}")
    print(f"  Removed:  {metrics['improvements']['excessive_blank_lines_removed']:,}")
    print()
    
    # Text Quality
    print("✨ TEXT QUALITY INDICATORS")
    print("-" * 80)
    print(f"Text Density (non-whitespace ratio):")
    print(f"  Original: {metrics['original']['text_density']:.4f}")
    print(f"  Cleaned:  {metrics['cleaned']['text_density']:.4f}")
    print(f"  Improvement: {'Higher is better - more content, less whitespace' if metrics['cleaned']['text_density'] > metrics['original']['text_density'] else 'Same or lower'}")
    print()
    
    # Token Efficiency
    print("🎯 LLM PROCESSING EFFICIENCY")
    print("-" * 80)
    print(f"Token Count (approximate):")
    print(f"  Original: {metrics['original']['token_count']:,}")
    print(f"  Cleaned:  {metrics['cleaned']['token_count']:,}")
    print(f"  Reduction: {metrics['improvements']['token_reduction']:,} ({metrics['improvements']['token_reduction_pct']:.2f}%)")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Characters reduced: {metrics['improvements']['char_reduction']:,} ({metrics['improvements']['char_reduction_pct']:.2f}%)")
    print(f"✅ Tokens reduced: {metrics['improvements']['token_reduction']:,} ({metrics['improvements']['token_reduction_pct']:.2f}%)")
    print(f"✅ Broken sentences fixed: {metrics['improvements']['single_newlines_fixed']:,}")
    print(f"✅ Multiple spaces normalized: {metrics['improvements']['multiple_spaces_reduced']:,}")
    print(f"✅ Tabs converted to spaces: {metrics['improvements']['tabs_removed']:,}")
    print(f"✅ Excessive blank lines removed: {metrics['improvements']['excessive_blank_lines_removed']:,}")
    print()
    
    if metrics['improvements']['token_reduction'] > 0:
        print(f"💡 The cleaned text uses {metrics['improvements']['token_reduction_pct']:.2f}% fewer tokens,")
        print(f"   which means lower processing costs and faster LLM responses!")
    print("=" * 80)

