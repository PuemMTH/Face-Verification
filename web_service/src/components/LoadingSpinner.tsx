import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner = ({ size = 'md' }: LoadingSpinnerProps) => {
  const dotSize = size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-6 h-6' : 'w-4 h-4';
  const containerSize = size === 'sm' ? 'min-h-[100px]' : size === 'lg' ? 'min-h-[300px]' : 'min-h-[200px]';

  return (
    <div className={`flex justify-center items-center ${containerSize}`}>
      <motion.div
        className="flex space-x-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {[0, 1, 2].map((index) => (
          <motion.div
            key={index}
            className={`${dotSize} bg-primary rounded-full`}
            animate={{
              y: [-10, 0, -10],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              delay: index * 0.2,
            }}
          />
        ))}
      </motion.div>
    </div>
  );
}; 