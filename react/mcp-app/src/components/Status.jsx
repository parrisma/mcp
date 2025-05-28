import React from 'react';
import Typography from '@mui/material/Typography';
import PropTypes from 'prop-types';

/**
 * Status component to display status messages.
 * @param {object} props - The component's props.
 * @param {string} props.message - The status message to display.
 * @returns {JSX.Element}
 */
function Status({ message }) {
return (
    <Typography
        component="pre"
        data-testid="status-message"
        sx={{
            border: 1,
            borderRadius: 1,
            p: 2,
            height: '200px', // Approx 10 lines depending on font size
            overflowY: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            userSelect: 'text',
        }}
        tabIndex={0}
        aria-readonly="true"
    >
        {message || 'No status message.'}
    </Typography>
);
}

Status.propTypes = {
  message: PropTypes.string,
};

Status.defaultProps = {
  message: '',
};

export default Status;